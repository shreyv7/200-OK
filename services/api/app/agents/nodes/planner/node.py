"""Micro-mission planner lens — AIS M4."""

from __future__ import annotations

from typing import Any

from app.services.recommendation.fallback_catalog import get_fallback_mission

_MISSION_TEMPLATES: dict[str, str] = {
    "execution": "Publish one small artifact today that proves forward motion",
    "confidence": "Share one unpolished clip with a trusted peer",
    "consistency": "Complete one 10-minute practice block before noon",
    "accountability": "Send a progress update to one accountability partner",
    "knowledge": "Teach one concept you learned this week in 3 bullets",
    "communication": "Deliver a 90-second structured update out loud",
    "focus": "Protect one distraction-free block for your top growth action",
    "networking": "Reach out to one person one step ahead on your path",
    "discipline": "Finish the smallest version of today's committed action",
    "burnout": "Take one restorative break, then do the smallest viable rep",
}


def build_planner_candidates(
    bottleneck: str,
    *,
    small_experiment: bool = False,
) -> list[dict[str, Any]]:
    title = _MISSION_TEMPLATES.get(bottleneck, _MISSION_TEMPLATES["execution"])
    if small_experiment:
        title = f"Small experiment: {title.lower()}"
    return [
        {
            "id": f"cand-mission-{bottleneck}",
            "type": "micro_mission",
            "title": title,
            "sourceBadge": "Curated fallback",
        }
    ]


def planner_node(state: dict[str, Any]) -> dict[str, Any]:
    bottleneck_packet = state.get("bottleneck_packet") or {}
    bottleneck = bottleneck_packet.get("bottleneck", "execution")
    small_experiment = bool(state.get("small_experiment"))
    candidates = build_planner_candidates(bottleneck, small_experiment=small_experiment)
    if not candidates:
        candidates = [get_fallback_mission(bottleneck, small_experiment=small_experiment)]
    return {
        "visited": ["planner"],
        "planner_candidates": candidates,
    }
