"""Leverage-moment feature extractor for AIA M8 (PRD §6 F9).

Extracts calendar proximity features to drive pre-event leverage interventions
before major upcoming events (e.g. college presentation, Friday).
"""

from datetime import datetime, timezone
from typing import Any, List, Optional

from app.schemas.identity import DeclaredSelf
from app.services.decision.packet import LeverageFeatures
from app.services.identity.sanitizer import get_event_delta_days


def _get_val(obj: Any, key: str, default: Any = None) -> Any:
    """Safely extracts value from dict or Pydantic object."""
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def extract_leverage_features(
    calendar_events: Optional[List[Any]] = None,
    declared_self: Optional[DeclaredSelf] = None,
    ref_time: Optional[datetime] = None,
) -> Optional[LeverageFeatures]:
    """Extracts LeverageFeatures for upcoming calendar events occurring within 0-7 days."""
    if not calendar_events:
        return None

    if ref_time is None:
        ref_time = datetime.now(timezone.utc)

    upcoming_candidates: List[tuple[float, Any]] = []

    for item in calendar_events:
        event_id = str(_get_val(item, "id", _get_val(item, "event_id", "evt_unk")))
        title = str(_get_val(item, "title", _get_val(item, "name", "")))
        start_ts = _get_val(item, "start_time", _get_val(item, "timestamp", None))

        if not title or start_ts is None:
            continue

        if isinstance(start_ts, str):
            try:
                start_dt = datetime.fromisoformat(start_ts)
            except Exception:
                continue
        elif isinstance(start_ts, datetime):
            start_dt = start_ts
        else:
            continue

        if start_dt.tzinfo is None:
            start_dt = start_dt.replace(tzinfo=timezone.utc)

        # Days until event
        delta_seconds = (start_dt - ref_time).total_seconds()
        days_until = delta_seconds / 86400.0

        if 0.0 < days_until <= 7.0:
            upcoming_candidates.append((days_until, item))

    if not upcoming_candidates:
        return None

    # Sort by closest event
    upcoming_candidates.sort(key=lambda x: x[0])
    closest_days, closest_event = upcoming_candidates[0]

    event_id = str(_get_val(closest_event, "id", _get_val(closest_event, "event_id", "evt_leverage_001")))
    title = str(_get_val(closest_event, "title", _get_val(closest_event, "name", "Upcoming Event")))
    attr_id = str(_get_val(closest_event, "attribute_id", _get_val(closest_event, "identityAttributeId", "")))

    # Fallback attribute matching if not provided directly
    if not attr_id and declared_self and declared_self.attributes:
        title_lower = title.lower()
        for attr in declared_self.attributes:
            if attr.id in title_lower or attr.label.lower() in title_lower:
                attr_id = attr.id
                break
        if not attr_id:
            attr_id = declared_self.attributes[0].id

    # Classify prep type
    title_lower = title.lower()
    if any(k in title_lower for k in ["presentation", "talk", "speaking", "speech", "pitch"]):
        prep_type = "rehearsal"
    elif any(k in title_lower for k in ["demo", "launch", "submission", "review", "commit"]):
        prep_type = "quick_review"
    else:
        prep_type = "mindset"

    return LeverageFeatures(
        has_upcoming_event=True,
        event_id=event_id,
        event_title=title,
        days_until_event=round(closest_days, 2),
        relevant_attribute_id=attr_id,
        suggested_prep_type=prep_type,
    )
