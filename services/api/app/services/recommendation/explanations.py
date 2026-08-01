"""Deterministic stack explanations — AIS M4."""

from __future__ import annotations

from app.schemas import StackExplanation


def build_explanation(
    *,
    bottleneck: str,
    element_type: str,
    title: str,
    source_badge: str,
    small_experiment: bool = False,
    capacity_tier: str = "full",
) -> StackExplanation:
    experiment_note = " Start with the smallest safe version." if small_experiment else ""
    if element_type == "micro_mission":
        return StackExplanation(
            whyThis=f"Targets the {bottleneck} bottleneck with a concrete action: {title}.{experiment_note}",
            whyNow="Gap invalidation or drift trigger requested a refreshed stack.",
            howReducesGap="Creation evidence raises Revealed Self toward the declared target.",
        )
    return StackExplanation(
        whyThis=f"Supports the current {bottleneck} bottleneck with matched learning: {title}.",
        whyNow=f"Paired with the action while capacity tier is {capacity_tier} ({source_badge}).",
        howReducesGap="Passive learning plus immediate application closes the say-do gap.",
    )
