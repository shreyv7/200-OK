"""Dead-letter filter and event sanitizer module for AIA evidence pipeline.

Consumes Backend Pydantic EvidenceEvent schema (app.schemas.evidence).
Validates raw evidence payloads and rejects corrupt, out-of-bounds, or malformed events.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple, Union

from app.schemas.evidence import EvidenceEvent, EventCategory, SourceProvider
from app.services.identity.scoring.constants import EVENT_WEIGHTS


def get_event_delta_days(timestamp: datetime, ref_time: Optional[datetime] = None) -> float:
    """Calculates age in days (delta_days >= 0.0) from timestamp relative to ref_time (UTC)."""
    if ref_time is None:
        ref_time = datetime.now(timezone.utc)
    elif ref_time.tzinfo is None:
        ref_time = ref_time.replace(tzinfo=timezone.utc)

    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)

    delta_seconds = (ref_time - timestamp).total_seconds()
    delta_days = delta_seconds / 86400.0
    return max(0.0, delta_days)


def validate_and_sanitize_event(raw: Union[Dict[str, Any], EvidenceEvent]) -> Tuple[bool, Optional[EvidenceEvent], Optional[str]]:
    """Validates raw dict or EvidenceEvent Pydantic instance.
    
    Returns (is_valid, EvidenceEvent, error_message).
    Rejects dead-letter / malformed payloads without throwing unhandled exceptions.
    """
    if isinstance(raw, EvidenceEvent):
        if not raw.userId or not raw.userId.strip():
            return False, None, "Missing or empty 'userId'"
        if not raw.type or not raw.type.strip():
            return False, None, "Missing or empty 'type'"
        return True, raw, None

    if not isinstance(raw, dict):
        return False, None, "Payload must be a dictionary or EvidenceEvent instance"

    user_id = raw.get("userId") or raw.get("user_id")
    if not user_id or not isinstance(user_id, str) or not user_id.strip():
        return False, None, "Missing or empty 'userId'"

    event_type = raw.get("type") or raw.get("event_type")
    if not event_type or not isinstance(event_type, str) or not event_type.strip():
        return False, None, "Missing or empty 'type'"

    event_id = str(raw.get("id") or raw.get("event_id") or f"evt_{hash(str(raw))}")
    source = raw.get("source", "trellis")
    category = raw.get("category", "passive_learning")
    base_weight = raw.get("baseWeight", raw.get("base_weight", EVENT_WEIGHTS.get(event_type, 1.0)))
    value = raw.get("value", base_weight)
    simulated = bool(raw.get("simulated", False))
    identity_attr_ids = raw.get("identityAttributeIds") or raw.get("identity_attribute_ids") or []
    metadata = raw.get("metadata") if isinstance(raw.get("metadata"), dict) else {}

    ts_raw = raw.get("timestamp")
    if isinstance(ts_raw, datetime):
        ts = ts_raw
    elif isinstance(ts_raw, str):
        try:
            ts = datetime.fromisoformat(ts_raw)
        except ValueError:
            ts = datetime.now(timezone.utc)
    else:
        ts = datetime.now(timezone.utc)

    try:
        event = EvidenceEvent(
            id=event_id,
            userId=user_id,
            timestamp=ts,
            source=source,
            type=event_type,
            category=category,
            identityAttributeIds=list(identity_attr_ids),
            value=float(value),
            baseWeight=float(base_weight),
            metadata=metadata,
            simulated=simulated,
        )
        return True, event, None
    except Exception as exc:
        return False, None, f"Failed to construct EvidenceEvent: {str(exc)}"
