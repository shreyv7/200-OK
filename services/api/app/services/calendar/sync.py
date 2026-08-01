"""Google Calendar Sync Service. Owner: Person D. D3 (F9, PRD §6).

Fetches upcoming events from Google Calendar API using the authenticated user's
access token (via D1 IntegrationRepository and D2 ensure_fresh_token), normalizes
them to EvidenceEvent records, ingests through the single evidence pipeline, and
upserts into the calendar_events table for plan-view queries.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

from sqlalchemy.orm import Session

if TYPE_CHECKING:
    from app.core.config import Settings

logger = logging.getLogger(__name__)

_SYNC_DAYS_AHEAD = 14
_MAX_RESULTS = 50


class GoogleCalendarSyncService:
    """Syncs upcoming Google Calendar events for a connected user.

    Designed to be called on-demand (e.g. on GET /calendar/plan-view) and
    later by a Celery beat task (Person C). All Google API calls are isolated
    within this class for easy mocking in tests.
    """

    def sync_upcoming_events(
        self,
        user_id: str,
        db: Session,
        settings: "Settings",
        days_ahead: int = _SYNC_DAYS_AHEAD,
    ) -> int:
        """Fetches and syncs upcoming calendar events for user_id.

        Returns the count of new EvidenceEvent rows created (deduped, so re-sync = 0).
        Returns 0 immediately if no active google-calendar connection exists.
        """
        from app.api.integrations import ensure_fresh_token
        from app.integrations.mcp.calendar.adapter import normalize_raw_google_event
        from app.repositories.calendar_repository import upsert_from_google_event
        from app.services.evidence import service as evidence_service

        try:
            conn = ensure_fresh_token(user_id, "google-calendar", db, settings)
        except Exception as exc:
            logger.warning(
                "google-calendar token refresh failed for user %s, skipping sync: %s",
                user_id,
                exc,
            )
            return 0

        if conn is None or not conn.is_active:
            return 0

        try:
            events = self._fetch_events(conn.access_token, days_ahead)
        except Exception as exc:
            logger.warning(
                "Google Calendar API fetch failed for user %s: %s", user_id, exc
            )
            return 0

        new_count = 0
        for raw_event in events:
            google_event_id = raw_event.get("id")
            if not google_event_id:
                continue

            # Normalize → EvidenceEvent (simulated=False)
            ev = normalize_raw_google_event(raw_event, user_id)

            # Ingest through the single evidence pipeline (idempotent)
            from app.services.evidence.service import request_from_event
            req = request_from_event(ev)
            _, created = evidence_service.ingest(db, req)
            if created:
                new_count += 1

            # Upsert into calendar_events for plan-view
            title = raw_event.get("summary", "Untitled Event")
            leverage_tag = self._infer_leverage_tag(title)
            upsert_from_google_event(
                db=db,
                user_id=user_id,
                source_event_id=google_event_id,
                title=title,
                event_time=ev.timestamp,
                leverage_tag=leverage_tag,
            )

        return new_count

    def _fetch_events(self, access_token: str, days_ahead: int) -> list:
        """Calls Google Calendar API and returns raw event dicts.

        Isolated here for easy mocking in tests via
        `patch.object(GoogleCalendarSyncService, "_fetch_events")`.
        """
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build

        creds = Credentials(token=access_token)
        service = build("calendar", "v3", credentials=creds, cache_discovery=False)

        now = datetime.now(timezone.utc)
        time_max = now + timedelta(days=days_ahead)

        result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=now.isoformat(),
                timeMax=time_max.isoformat(),
                singleEvents=True,
                orderBy="startTime",
                maxResults=_MAX_RESULTS,
            )
            .execute()
        )
        return result.get("items", [])

    @staticmethod
    def _infer_leverage_tag(title: str) -> str | None:
        """Infers a leverage tag from event title for plan-view feature (F9)."""
        title_lower = title.lower()
        if any(k in title_lower for k in ["presentation", "talk", "speech", "pitch", "toastmasters"]):
            return "public_speaker"
        if any(k in title_lower for k in ["demo", "build", "project", "commit", "deploy", "launch"]):
            return "builder"
        if any(k in title_lower for k in ["interview", "review", "evaluation", "assessment"]):
            return "professional_growth"
        return None
