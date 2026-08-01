"""Google Calendar MCP Adapter. Owner: Person D. D3 (F9, PRD §6, milestones.md M8).

Normalizes raw Google Calendar API event dicts to canonical EvidenceEvent records
with simulated=False — marking them as real, live data from the user's calendar.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict

from app.integrations.mcp.base import EvidenceAdapter
from app.schemas.evidence import EvidenceEvent, RawMCPPayload
from app.services.identity.scoring.constants import EVENT_WEIGHTS

_TYPE = "attended_experience"


def _parse_event_time(start_dict: Dict[str, Any]) -> datetime:
    """Parses Google Calendar event start time.

    Handles both dateTime (timed events) and date (all-day events).
    All-day events use noon UTC as a safe representative time.
    """
    if "dateTime" in start_dict:
        dt = datetime.fromisoformat(start_dict["dateTime"])
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt

    # All-day event: start.date is "YYYY-MM-DD"
    date_str = start_dict.get("date", "")
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return datetime.now(timezone.utc)
    # Use noon UTC as representative time for all-day events
    return d.replace(hour=12, minute=0, second=0, tzinfo=timezone.utc)


def normalize_raw_google_event(raw_event: Dict[str, Any], user_id: str) -> EvidenceEvent:
    """Converts a Google Calendar API event dict to a canonical EvidenceEvent.

    Key properties of the resulting event:
    - simulated=False: This is live data, never a fixture or seed
    - source="google_calendar": Provider-driven, satisfies D5 honesty flag requirement
    - category="creation": Calendar events are treated as intentional creation actions
    """
    start_dict = raw_event.get("start", {})
    event_time = _parse_event_time(start_dict)
    title = raw_event.get("summary", "Untitled Event")
    google_event_id = raw_event.get("id", str(uuid.uuid4()))
    organizer_email = raw_event.get("organizer", {}).get("email", "")

    return EvidenceEvent(
        id=str(uuid.uuid4()),
        userId=user_id,
        timestamp=event_time,
        source="google_calendar",
        type=_TYPE,
        category="creation",
        identityAttributeIds=[],
        value=1.0,
        baseWeight=EVENT_WEIGHTS.get(_TYPE, 4.0),
        metadata={
            "google_event_id": google_event_id,
            "title": title,
            "calendar_id": organizer_email,
        },
        simulated=False,
    )


class CalendarEventAdapter(EvidenceAdapter):
    """Adapter that normalizes a Google Calendar event payload to an EvidenceEvent.

    Wraps normalize_raw_google_event() to satisfy the EvidenceAdapter ABC interface
    for backward-compatible usage with the simulator/seed fixture pattern.
    """

    def __init__(self, user_id: str) -> None:
        self._user_id = user_id

    def normalize(self, payload: RawMCPPayload) -> EvidenceEvent:
        return normalize_raw_google_event(payload.rawPayload, self._user_id)
