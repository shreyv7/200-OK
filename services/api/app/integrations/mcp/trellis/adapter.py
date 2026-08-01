"""Fixture Trellis-native adapter. Owner: Backend.

Used by the simulator (doomscroll burst / time advance) and the seed
script for in-app event types that don't come from an external MCP
provider. Event-type strings and weights are sourced from AIA's frozen
Gap formula constants (app.services.identity.scoring.constants) — the
single source of truth the deterministic Gap math keys off of. Backend
must speak that vocabulary exactly; duplicating it here caused a real
M1 bug where "focus_drift"/"passive_item_completed" silently failed to
match CREATION_TYPES/PASSIVE_TYPES/DRIFT_TYPES (fixed in M2).
"""

from __future__ import annotations

import uuid
from datetime import datetime

from app.integrations.mcp.base import EvidenceAdapter
from app.schemas.evidence import EvidenceEvent, RawMCPPayload
from app.services.identity.scoring.constants import EVENT_WEIGHTS

_CATEGORY_BY_TYPE = {
    "mission_completed": "creation",
    "passive_item": "passive_learning",
    "focus_drift_10min": "focus_drift",
}


class FixtureTrellisAdapter(EvidenceAdapter):
    """Maps in-app fixture events (simulator/seed) to canonical EvidenceEvents."""

    def normalize(self, payload: RawMCPPayload) -> EvidenceEvent:
        raw = payload.rawPayload
        event_type = raw["type"]
        if event_type not in _CATEGORY_BY_TYPE:
            raise ValueError(f"Unsupported trellis fixture type: {event_type}")

        timestamp = raw["timestamp"]
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)

        units = raw.get("units", 1.0)

        return EvidenceEvent(
            id=str(uuid.uuid4()),
            userId=raw["userId"],
            timestamp=timestamp,
            source="trellis",
            type=event_type,
            category=_CATEGORY_BY_TYPE[event_type],
            identityAttributeIds=raw.get("identityAttributeIds", []),
            value=units,
            baseWeight=EVENT_WEIGHTS[event_type],
            metadata=raw.get("metadata", {}),
            simulated=raw.get("simulated", True),
        )
