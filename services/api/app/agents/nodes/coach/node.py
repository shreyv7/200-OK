from __future__ import annotations

from typing import Any

from app.services.identity.scoring.constants import CAPACITY_LIGHT_MIN


def _coach_allowed(state: dict[str, Any]) -> bool:
    if not state.get("delivery_allowed", True):
        return False
    decision = state.get("guardian_decision") or {}
    action = decision.get("action")
    if action in {"cancel", "delay"}:
        return False
    capacity_pct = int(state.get("capacity_pct", 100))
    return capacity_pct >= CAPACITY_LIGHT_MIN


def coach_node(state: dict[str, Any]) -> dict[str, Any]:
    """Execution Coach — P2; only speaks when Guardian allows delivery."""
    if not _coach_allowed(state):
        return {"visited": ["coach"]}

    decision = state.get("guardian_decision") or {}
    return {
        "visited": ["coach"],
        "coach_message": {
            "text": "Stay focused on the smallest next move that matches your declared identity.",
            "intensity": decision.get("intensity", "full"),
        },
    }
