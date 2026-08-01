from __future__ import annotations

import os
from typing import Any


def _fixture_invalidate_enabled() -> bool:
    """Fixture-only invalidation flag for M1 (no real ranking)."""
    return os.environ.get("AIS_M1_FIXTURE_INVALIDATE", "false").lower() == "true"


def coordinator_node(state: dict[str, Any]) -> dict[str, Any]:
    packet = state.get("decision_packet") or {}
    invalidate = bool(packet.get("invalidateStack")) or _fixture_invalidate_enabled()
    hypothesis_id = state.get("hypothesis_id") or f"hyp-{state.get('run_id', 'pending')}"

    return {
        "visited": ["coordinator"],
        "stack_draft": {
            "invalidate": invalidate,
            "hypothesis_id": hypothesis_id,
        },
    }
