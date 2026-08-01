from __future__ import annotations

import os
from typing import Any


def _fixture_invalidate_enabled() -> bool:
    """Test-only override — production path uses DecisionPacket.invalidateStack."""
    return os.environ.get("AIS_M1_FIXTURE_INVALIDATE", "false").lower() == "true"


def coordinator_node(state: dict[str, Any]) -> dict[str, Any]:
    packet = state.get("decision_packet") or {}
    invalidate = bool(packet.get("invalidateStack")) or _fixture_invalidate_enabled()
    invalidated_element_ids = list(packet.get("invalidatedElementIds") or [])
    hypothesis_id = state.get("hypothesis_id") or f"hyp-{state.get('run_id', 'pending')}"

    return {
        "visited": ["coordinator"],
        "stack_draft": {
            "invalidate": invalidate,
            "invalidated_element_ids": invalidated_element_ids,
            "hypothesis_id": hypothesis_id,
        },
    }
