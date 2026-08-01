"""Notion Sync Service. Owner: Person D.

Fetches recently created/edited pages from Notion API v2 via POST /v1/search
using the authenticated user's access token (via IntegrationRepository and ensure_fresh_token),
normalizes them to EvidenceEvent records (simulated=False), and ingests them through
the single evidence pipeline.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any, Dict, List

import httpx
from sqlalchemy.orm import Session

if TYPE_CHECKING:
    from app.core.config import Settings

logger = logging.getLogger(__name__)

_DEFAULT_DAYS_BACK = 30
_MAX_RESULTS = 50


class NotionSyncService:
    """Syncs recent Notion page activity (created/edited pages) for a connected user.

    Designed to be triggered on-demand via POST /api/v1/notion/sync and
    periodically via Celery worker/beat. All Notion API interaction
    is isolated in `_fetch_pages` for clean mocking in tests.
    """

    def sync_recent_pages(
        self,
        user_id: str,
        db: Session,
        settings: "Settings",
        days_back: int = _DEFAULT_DAYS_BACK,
    ) -> int:
        """Fetches and syncs recently created or edited pages for user_id.

        Returns the count of new EvidenceEvent rows created (deduped, so re-sync = 0).
        Returns 0 immediately if no active notion connection exists.
        """
        from app.api.integrations import ensure_fresh_token
        from app.integrations.mcp.notion.adapter import (
            normalize_raw_notion_page,
            normalize_raw_notion_page_edit,
            _parse_notion_time,
        )
        from app.services.evidence import service as evidence_service
        from app.services.evidence.service import request_from_event

        try:
            conn = ensure_fresh_token(user_id, "notion", db, settings)
        except Exception as exc:
            logger.warning(
                "notion token refresh failed for user %s, skipping sync: %s",
                user_id,
                exc,
            )
            return 0

        if conn is None or not conn.is_active:
            return 0

        try:
            raw_pages = self._fetch_pages(conn.access_token, days_back)
        except Exception as exc:
            logger.warning("Notion API search failed for user %s: %s", user_id, exc)
            return 0

        new_count = 0
        for page in raw_pages:
            created_dt = _parse_notion_time(page.get("created_time"))
            edited_dt = _parse_notion_time(page.get("last_edited_time"))

            # If created and last_edited are within 60s, consider it a new creation
            diff_sec = abs((edited_dt - created_dt).total_seconds())
            if diff_sec <= 60:
                ev = normalize_raw_notion_page(page, user_id)
            else:
                ev = normalize_raw_notion_page_edit(page, user_id)

            req = request_from_event(ev)
            _, created = evidence_service.ingest(db, req)
            if created:
                new_count += 1

        return new_count

    def _fetch_pages(self, access_token: str, days_back: int) -> List[Dict[str, Any]]:
        """Calls Notion API /v1/search to list recently edited pages.

        Isolated for test mocking via `patch.object(NotionSyncService, "_fetch_pages")`.
        """
        since_dt = datetime.now(timezone.utc) - timedelta(days=days_back)
        since_str = since_dt.isoformat()

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
        }
        payload = {
            "filter": {"value": "page", "property": "object"},
            "sort": {"direction": "descending", "timestamp": "last_edited_time"},
            "page_size": _MAX_RESULTS,
        }

        with httpx.Client(timeout=10.0) as client:
            resp = client.post("https://api.notion.com/v1/search", json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        results = data.get("results", [])
        # Filter to pages edited since `days_back`
        filtered = []
        for page in results:
            edited_time = page.get("last_edited_time", "")
            if edited_time and edited_time >= since_str[:10]:
                filtered.append(page)

        return filtered
