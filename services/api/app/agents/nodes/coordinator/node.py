from __future__ import annotations

import os
from typing import Any

from app.services.recommendation.diagnose_consume import consume_bottleneck_diagnosis


def _fixture_invalidate_enabled() -> bool:
    """Test-only override — production path uses DecisionPacket.invalidateStack."""
    return os.environ.get("AIS_M1_FIXTURE_INVALIDATE", "false").lower() == "true"


def coordinator_node(state: dict[str, Any]) -> dict[str, Any]:
    trigger = state.get("trigger", "")
    packet = state.get("decision_packet") or {}
    invalidate = (
        bool(packet.get("invalidateStack"))
        or _fixture_invalidate_enabled()
        or trigger == "onboarding.confirmed"
    )
    invalidated_element_ids = list(packet.get("invalidatedElementIds") or [])
    hypothesis_id = state.get("hypothesis_id") or f"hyp-{state.get('run_id', 'pending')}"

    diagnosis = consume_bottleneck_diagnosis(packet)

    return {
        "visited": ["coordinator"],
        "stack_draft": {
            "invalidate": invalidate,
            "invalidated_element_ids": invalidated_element_ids,
            "hypothesis_id": hypothesis_id,
        },
        "bottleneck_packet": diagnosis["bottleneck_packet"],
        "small_experiment": diagnosis["small_experiment"],
    }
