"""Stack replacement policy — keep valid, replace stale/failed/mismatched — AIS M4."""

from __future__ import annotations

from typing import Any

from app.schemas import IdentityStack, StackElement

RESOURCE_TYPES = frozenset({"media", "knowledge", "growth_story", "tool"})


def _element_dict(element: StackElement) -> dict[str, Any]:
    return element.model_dump()


def _should_keep_element(
    element: StackElement,
    *,
    bottleneck: str,
    invalidated_ids: set[str],
    invalidate_all: bool,
) -> bool:
    if invalidate_all:
        return False
    if element.id in invalidated_ids:
        return False
    if element.type == "micro_mission":
        return True
    return element.type in RESOURCE_TYPES


def apply_replacement_policy(
    prior_stack: IdentityStack | None,
    *,
    bottleneck: str,
    invalidate_stack: bool,
    invalidated_element_ids: list[str],
    knowledge_candidates: list[dict[str, Any]],
    planner_candidates: list[dict[str, Any]],
    fallback_knowledge: dict[str, Any],
    fallback_mission: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return chosen resource + mission candidates after replacement policy."""
    invalidated_ids = set(invalidated_element_ids)
    invalidate_all = invalidate_stack and not invalidated_ids

    kept_mission: dict[str, Any] | None = None
    kept_resource: dict[str, Any] | None = None

    if prior_stack is not None and not invalidate_all:
        for element in prior_stack.elements:
            if not _should_keep_element(
                element,
                bottleneck=bottleneck,
                invalidated_ids=invalidated_ids,
                invalidate_all=False,
            ):
                continue
            data = _element_dict(element)
            if element.type == "micro_mission" and kept_mission is None:
                kept_mission = data
            elif element.type in RESOURCE_TYPES and kept_resource is None:
                kept_resource = data

    mission = kept_mission or (planner_candidates[0] if planner_candidates else fallback_mission)
    resource = kept_resource or (knowledge_candidates[0] if knowledge_candidates else fallback_knowledge)

    return resource, mission
