"""Dead-letter filter and event sanitizer module for AIA evidence pipeline.

Validates raw evidence payloads and rejects corrupt, out-of-bounds, or malformed events.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple

from app.services.identity.scoring.constants import EVENT_WEIGHTS


@dataclass
class SanitizedEvent:
    event_id: str
    user_id: str
    event_type: str
    attr_id: str
    a_ik: float  # Applicability in [0.0, 1.0]
    delta_days: float  # Age in days (>= 0.0)
    value_override: Optional[float] = None
    source: str = "app"
    simulated: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


def validate_and_sanitize_event(raw: Dict[str, Any]) -> Tuple[bool, Optional[SanitizedEvent], Optional[str]]:
    """Validates raw evidence dictionary and returns (is_valid, SanitizedEvent, error_message).
    
    Rejects malformed, corrupt, or out-of-bounds evidence payloads before scoring.
    """
    if not isinstance(raw, dict):
        return False, None, "Payload must be a dictionary"

    user_id = raw.get("user_id")
    if not user_id or not isinstance(user_id, str):
        return False, None, "Missing or invalid 'user_id'"

    event_type = raw.get("event_type")
    if not event_type or not isinstance(event_type, str):
        return False, None, "Missing or invalid 'event_type'"

    if event_type not in EVENT_WEIGHTS and "value_override" not in raw:
        return False, None, f"Unknown event_type '{event_type}' without value_override"

    delta_days = raw.get("delta_days", 0.0)
    try:
        delta_days = float(delta_days)
    except (ValueError, TypeError):
        return False, None, "Invalid 'delta_days', must be numeric"

    if delta_days < 0.0:
        return False, None, "Negative 'delta_days' is not allowed"

    a_ik = raw.get("a_ik", 1.0)
    try:
        a_ik = float(a_ik)
    except (ValueError, TypeError):
        return False, None, "Invalid 'a_ik', must be numeric"

    if not (0.0 <= a_ik <= 1.0):
        return False, None, f"'a_ik' out of bounds [0.0, 1.0]: {a_ik}"

    value_override = raw.get("value_override")
    if value_override is not None:
        try:
            value_override = float(value_override)
        except (ValueError, TypeError):
            return False, None, "Invalid 'value_override', must be numeric"

    event_id = str(raw.get("event_id") or raw.get("id") or f"evt_{hash(str(raw))}")
    attr_id = str(raw.get("attr_id") or raw.get("identity_attribute_id") or "unmapped")
    source = str(raw.get("source", "app"))
    simulated = bool(raw.get("simulated", False))
    metadata = raw.get("metadata") if isinstance(raw.get("metadata"), dict) else {}

    sanitized = SanitizedEvent(
        event_id=event_id,
        user_id=user_id,
        event_type=event_type,
        attr_id=attr_id,
        a_ik=a_ik,
        delta_days=delta_days,
        value_override=value_override,
        source=source,
        simulated=simulated,
        metadata=metadata,
    )

    return True, sanitized, None
