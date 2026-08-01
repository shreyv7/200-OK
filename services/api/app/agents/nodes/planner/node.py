"""Micro-mission planner lens — AIS M4."""

from __future__ import annotations

from typing import Any

from app.services.recommendation.planner_missions import build_planner_candidates


def planner_node(state: dict[str, Any]) -> dict[str, Any]:
    bottleneck_packet = state.get("bottleneck_packet") or {}
    bottleneck = bottleneck_packet.get("bottleneck", "execution")
    candidates = build_planner_candidates(
        bottleneck,
        small_experiment=bool(state.get("small_experiment")),
        bottleneck_confidence=bottleneck_packet.get("confidence"),
        user_id=state.get("user_id"),
        db=state.get("db_session"),
    )
    return {
        "visited": ["planner"],
        "planner_candidates": candidates,
    }
