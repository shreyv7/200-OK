"""Notion MCP Adapter (Fixture and Live). Owner: Person D.

Provides:
1. FixtureNotionAdapter: Maps simulated Notion page fixtures (simulated=True) for CI/seed.
2. LiveNotionAdapter & normalizers: Maps real Notion API page dicts (simulated=False).

Evidence mapping (PRD §9):
  - notion_page_created → category=creation, baseWeight=3.0 (creating a new page)
  - notion_page_edited  → category=creation, baseWeight=1.5 (editing an existing page)
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict

from app.integrations.mcp.base import EvidenceAdapter
from app.schemas.evidence import EvidenceEvent, RawMCPPayload
from app.services.identity.scoring.constants import EVENT_WEIGHTS

_CREATED_TYPE = "notion_page_created"
_EDITED_TYPE = "notion_page_edited"

# If created_time and last_edited_time differ by less than this, treat as "created" not "edited"
_CREATED_VS_EDITED_THRESHOLD_SECONDS = 60


def _extract_title(raw_page: Dict[str, Any]) -> str:
    """Extracts plain-text title from a Notion page properties dict.

    Notion stores titles as a rich-text array under properties.title.title[].plain_text.
    Falls back to "Untitled Page" if the structure is absent.
    """
    try:
        title_prop = raw_page.get("properties", {}).get("title", {})
        rich_text = title_prop.get("title", [])
        return "".join(part.get("plain_text", "") for part in rich_text) or "Untitled Page"
    except Exception:
        return "Untitled Page"


def _parse_notion_time(time_str: str | None) -> datetime:
    """Parses a Notion ISO 8601 timestamp string to a timezone-aware datetime."""
    if not time_str:
        return datetime.now(timezone.utc)
    try:
        dt = datetime.fromisoformat(time_str.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, AttributeError):
        return datetime.now(timezone.utc)


def normalize_raw_notion_page(raw_page: Dict[str, Any], user_id: str) -> EvidenceEvent:
    """Converts a newly created Notion page dict to a canonical EvidenceEvent.

    Key properties:
    - simulated=False: live data from the user's Notion workspace
    - source="notion": provider-driven, satisfies D5 honesty flag requirement
    - category="creation": creating a new page is an active creation signal
    - type="notion_page_created", baseWeight=3.0
    """
    page_id = raw_page.get("id", str(uuid.uuid4()))
    created_time = _parse_notion_time(raw_page.get("created_time"))
    title = _extract_title(raw_page)
    url = raw_page.get("url", "")
    parent_type = raw_page.get("parent", {}).get("type", "")

    return EvidenceEvent(
        id=str(uuid.uuid4()),
        userId=user_id,
        timestamp=created_time,
        source="notion",
        type=_CREATED_TYPE,
        category="creation",
        identityAttributeIds=[],
        value=1.0,
        baseWeight=EVENT_WEIGHTS.get(_CREATED_TYPE, 3.0),
        metadata={
            "notion_page_id": page_id,
            "title": title,
            "url": url,
            "parent_type": parent_type,
        },
        simulated=False,
    )


def normalize_raw_notion_page_edit(raw_page: Dict[str, Any], user_id: str) -> EvidenceEvent:
    """Converts a recently edited Notion page dict to a canonical EvidenceEvent.

    Key properties:
    - simulated=False: live data from the user's Notion workspace
    - source="notion": provider-driven, satisfies D5 honesty flag requirement
    - category="creation": editing knowledge is still an active creation signal
    - type="notion_page_edited", baseWeight=1.5
    """
    page_id = raw_page.get("id", str(uuid.uuid4()))
    edited_time = _parse_notion_time(raw_page.get("last_edited_time"))
    title = _extract_title(raw_page)
    url = raw_page.get("url", "")
    parent_type = raw_page.get("parent", {}).get("type", "")

    return EvidenceEvent(
        id=str(uuid.uuid4()),
        userId=user_id,
        timestamp=edited_time,
        source="notion",
        type=_EDITED_TYPE,
        category="creation",
        identityAttributeIds=[],
        value=1.0,
        baseWeight=EVENT_WEIGHTS.get(_EDITED_TYPE, 1.5),
        metadata={
            "notion_page_id": page_id,
            "title": title,
            "url": url,
            "parent_type": parent_type,
        },
        simulated=False,
    )


class FixtureNotionAdapter(EvidenceAdapter):
    """Maps a Notion-shaped fixture payload to a canonical EvidenceEvent (simulated=True).

    Used by the seed script and simulator to inject Notion evidence without real credentials.
    """

    def normalize(self, payload: RawMCPPayload) -> EvidenceEvent:
        raw = payload.rawPayload
        timestamp = raw.get("timestamp", datetime.now(timezone.utc).isoformat())
        if isinstance(timestamp, str):
            timestamp = _parse_notion_time(timestamp)

        return EvidenceEvent(
            id=str(uuid.uuid4()),
            userId=raw["userId"],
            timestamp=timestamp,
            source="notion",
            type=raw.get("type", _CREATED_TYPE),
            category="creation",
            identityAttributeIds=raw.get("identityAttributeIds", []),
            value=1.0,
            baseWeight=EVENT_WEIGHTS.get(raw.get("type", _CREATED_TYPE), 3.0),
            metadata={
                "notion_page_id": raw.get("notion_page_id", ""),
                "title": raw.get("title", "Untitled Page"),
                "url": raw.get("url", ""),
            },
            simulated=True,
        )


class LiveNotionAdapter(EvidenceAdapter):
    """Adapter for live Notion page events (simulated=False).

    Dispatches to normalize_raw_notion_page (created) or normalize_raw_notion_page_edit (edited)
    based on the time difference between created_time and last_edited_time.
    """

    def __init__(self, user_id: str) -> None:
        self._user_id = user_id

    def normalize(self, payload: RawMCPPayload) -> EvidenceEvent:
        raw = payload.rawPayload
        created_time = _parse_notion_time(raw.get("created_time"))
        edited_time = _parse_notion_time(raw.get("last_edited_time"))

        diff_seconds = abs((edited_time - created_time).total_seconds())
        if diff_seconds <= _CREATED_VS_EDITED_THRESHOLD_SECONDS:
            return normalize_raw_notion_page(raw, self._user_id)
        return normalize_raw_notion_page_edit(raw, self._user_id)
