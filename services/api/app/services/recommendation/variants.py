"""Intervention variant generation — full/light/micro, same hypothesis ID — AIS M5."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone

from app.schemas import IdentityStack, InterventionVariant, StackElement
from app.schemas.stack import VariantIntensity


def _clone_element(element: StackElement, *, title: str | None = None) -> StackElement:
    data = element.model_dump()
    if title is not None:
        data["title"] = title
    return StackElement.model_validate(data)


def _stack_for_intensity(stack: IdentityStack, intensity: VariantIntensity) -> IdentityStack:
    elements = list(stack.elements)
    mission = next((e for e in elements if e.type == "micro_mission"), elements[0])
    resource = next(
        (e for e in elements if e.type in {"media", "knowledge"}),
        elements[-1],
    )

    if intensity == "full":
        chosen = elements
    elif intensity == "light":
        chosen = [
            _clone_element(mission, title=f"Light version: {mission.title}"),
            resource,
        ]
    else:
        chosen = [
            _clone_element(
                mission,
                title=f"60-second mental rehearsal: {mission.title.lower()}",
            ),
        ]

    return IdentityStack(
        id=stack.id,
        userId=stack.userId,
        hypothesisId=stack.hypothesisId,
        bottleneck=stack.bottleneck,
        elements=chosen,
        curatedAt=stack.curatedAt,
        validUntil=stack.validUntil,
    )


def generate_variants(stack: IdentityStack) -> list[InterventionVariant]:
    """Generate full/light/micro variants sharing the active hypothesis ID."""
    now = datetime.now(timezone.utc)
    variants: list[InterventionVariant] = []
    for intensity in ("full", "light", "micro"):
        variants.append(
            InterventionVariant(
                hypothesisId=stack.hypothesisId,
                intensity=intensity,
                stack=_stack_for_intensity(stack, intensity),
                generatedAt=now,
            )
        )
    return variants


def select_variant_by_intensity(
    variants: list[InterventionVariant],
    intensity: VariantIntensity,
) -> InterventionVariant:
    for variant in variants:
        if variant.intensity == intensity:
            return variant
    return variants[-1]


def select_variant_by_capacity(
    variants: list[InterventionVariant],
    capacity_pct: int,
) -> InterventionVariant:
    from app.services.recommendation.guardian import capacity_to_intensity

    return select_variant_by_intensity(variants, capacity_to_intensity(capacity_pct))
