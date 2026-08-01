"""Deterministic stack explanations — AIS M4/M6."""

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
    tags: dict[str, str] | None = None,
) -> StackExplanation:
    if element_type in {"growth_story", "tool", "mentor", "real_world_experience"}:
        return build_catalog_explanation(
            bottleneck=bottleneck,
            element_type=element_type,
            title=title,
            source_badge=source_badge,
            tags=tags or {},
            capacity_tier=capacity_tier,
        )

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


def build_catalog_explanation(
    *,
    bottleneck: str,
    element_type: str,
    title: str,
    source_badge: str,
    tags: dict[str, str],
    capacity_tier: str = "full",
) -> StackExplanation:
    outcome = tags.get("outcome", "meaningful progress")
    if element_type == "growth_story":
        why_this = (
            f"This creator faced the same bottleneck you're facing today: {bottleneck}. "
            f"Their journey ended with {outcome.replace('_', ' ')}."
        )
    elif element_type == "mentor":
        why_this = (
            f"This mentor's journey matches your {bottleneck} bottleneck at the {tags.get('stage', 'current')} stage."
        )
    elif element_type == "tool":
        why_this = (
            f"This tool removes friction for your {bottleneck} bottleneck and enables the micro-mission."
        )
    else:
        why_this = (
            f"This experience targets your {bottleneck} bottleneck in a real-world setting: {title}."
        )
    return StackExplanation(
        whyThis=why_this,
        whyNow=f"Selected when capacity tier is {capacity_tier} ({source_badge}).",
        howReducesGap="Matched stage and bottleneck increase Alignment without generic filler.",
    )
