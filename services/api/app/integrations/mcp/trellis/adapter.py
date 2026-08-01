"""Fixture Trellis-native adapter. Owner: Backend.

Used by the simulator (doomscroll burst / time advance) and the seed
script for in-app event types that don't come from an external MCP
provider. Weight constants mirror prd.md §9 fixed evidence weights —
never invented at call time.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from app.integrations.mcp.base import EvidenceAdapter
from app.schemas.evidence import EvidenceEvent, RawMCPPayload

MISSION_COMPLETED_WEIGHT = 3.0
PASSIVE_ITEM_WEIGHT = 1.0
FOCUS_DRIFT_WEIGHT_PER_10MIN = -2.0

_CATEGORY_BY_TYPE = {
    "mission_completed": "creation",
    "passive_item_completed": "passive_learning",
    "focus_drift": "focus_drift",
}

_WEIGHT_BY_TYPE = {
    "mission_completed": MISSION_COMPLETED_WEIGHT,
    "passive_item_completed": PASSIVE_ITEM_WEIGHT,
    "focus_drift": FOCUS_DRIFT_WEIGHT_PER_10MIN,
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
            baseWeight=_WEIGHT_BY_TYPE[event_type],
            metadata=raw.get("metadata", {}),
            simulated=raw.get("simulated", True),
        )
