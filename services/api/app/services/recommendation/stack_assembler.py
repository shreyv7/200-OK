"""Identity Stack assembler — smallest coherent combination — AIS M4."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.schemas import DecisionPacket, IdentityStack, StackElement
from app.providers.llm.base import LLMProvider
from app.providers.search.base import SearchProvider
from app.services.recommendation.curation_context import get_curation_llm, get_curation_search
from app.services.recommendation.badge_mapping import document_source_to_badge
from app.services.recommendation.explanations import build_explanation
from app.services.recommendation.catalog import CatalogSource
from app.services.recommendation.catalog_ranking import (
    catalog_item_to_candidate,
    rank_catalog_items,
    select_catalog_element,
)
from app.services.recommendation.fallback_catalog import get_fallback_knowledge, get_fallback_mission
from app.services.recommendation.replacement import apply_replacement_policy
from app.services.recommendation.stage_feature import stage_from_ranking_features

MAX_STACK_ELEMENTS = 4


def build_providers(
    llm: LLMProvider | None = None,
    search: SearchProvider | None = None,
) -> tuple[LLMProvider, SearchProvider]:
    """Factory seam for DI; Backend Depends() will inject real providers."""
    return llm or get_curation_llm(), search or get_curation_search()


def _normalize_knowledge_candidate(candidate: dict[str, Any], index: int) -> dict[str, Any]:
    """Accept AIS candidate dicts or Backend SearchProvider Document dumps."""
    if "type" in candidate:
        normalized = dict(candidate)
        if "sourceBadge" not in normalized:
            normalized["sourceBadge"] = document_source_to_badge(
                str(normalized.get("source", "curated_fallback"))
            )
        if "id" not in normalized:
            normalized["id"] = f"cand-media-{index}"
        return normalized

    return {
        "id": candidate.get("id") or f"cand-media-{index}",
        "type": "media",
        "title": candidate.get("title") or "Growth resource",
        "url": candidate.get("url"),
        "sourceBadge": document_source_to_badge(str(candidate.get("source", "curated_fallback"))),
        "extract": candidate.get("extract"),
        "metadata": candidate.get("metadata", {}),
    }


def _normalize_knowledge_candidates(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [_normalize_knowledge_candidate(candidate, index) for index, candidate in enumerate(candidates)]


def _candidate_to_element(
    candidate: dict[str, Any],
    *,
    bottleneck: str,
    small_experiment: bool,
    capacity_tier: str,
) -> StackElement:
    element_type = candidate["type"]
    source_badge = candidate.get("sourceBadge", "Curated fallback")
    title = candidate["title"]
    return StackElement(
        id=candidate["id"],
        type=element_type,
        title=title,
        url=candidate.get("url"),
        sourceBadge=source_badge,
        explanation=build_explanation(
            bottleneck=bottleneck,
            element_type=element_type,
            title=title,
            source_badge=source_badge,
            small_experiment=small_experiment and element_type == "micro_mission",
            capacity_tier=capacity_tier,
            tags=candidate.get("tags"),
        ),
        metadata=candidate.get("metadata", {}),
    )


def resolve_stage(decision_packet: DecisionPacket) -> str:
    return stage_from_ranking_features(decision_packet.rankingFeatures)


def _select_justified_catalog_candidate(
    *,
    catalog_source: CatalogSource | None,
    bottleneck: str,
    stage: str,
) -> dict[str, Any] | None:
    if catalog_source is None:
        return None
    items = [
        item
        for item in catalog_source.fetch(bottleneck=bottleneck, stage=stage)
        if item.type in {"growth_story", "tool", "mentor"}
    ]
    ranked = rank_catalog_items(items, bottleneck=bottleneck, stage=stage)
    selected = select_catalog_element(ranked)
    if selected is None:
        return None
    return catalog_item_to_candidate(selected)


def _select_justified_opportunity_candidate(
    candidates: list[dict[str, Any]],
    *,
    bottleneck: str,
) -> dict[str, Any] | None:
    for candidate in candidates:
        tags = candidate.get("tags") or {}
        if tags.get("bottleneck") == bottleneck:
            return candidate
    return None


def assemble_identity_stack(
    decision_packet: DecisionPacket,
    *,
    knowledge_candidates: list[dict[str, Any]],
    planner_candidates: list[dict[str, Any]],
    prior_stack: IdentityStack | None = None,
    capacity_tier: str = "full",
    run_id: str | None = None,
    small_experiment: bool = False,
    catalog_source: CatalogSource | None = None,
    stage: str | None = None,
    opportunity_candidates: list[dict[str, Any]] | None = None,
    include_p1_lenses: bool = False,
) -> IdentityStack:
    """Assemble the smallest coherent stack (≥1 action + ≥1 resource). Never empty."""
    bottleneck = (
        decision_packet.bottleneck.bottleneck
        if decision_packet.bottleneck is not None
        else "execution"
    )
    fallback_knowledge = get_fallback_knowledge(bottleneck)
    fallback_mission = get_fallback_mission(bottleneck, small_experiment=small_experiment)

    if not knowledge_candidates:
        knowledge_candidates = [fallback_knowledge]
    else:
        knowledge_candidates = _normalize_knowledge_candidates(knowledge_candidates)
    if not planner_candidates:
        planner_candidates = [fallback_mission]

    resource, mission = apply_replacement_policy(
        prior_stack,
        bottleneck=bottleneck,
        invalidate_stack=decision_packet.invalidateStack,
        invalidated_element_ids=decision_packet.invalidatedElementIds,
        knowledge_candidates=knowledge_candidates,
        planner_candidates=planner_candidates,
        fallback_knowledge=fallback_knowledge,
        fallback_mission=fallback_mission,
    )

    elements = [
        _candidate_to_element(
            mission,
            bottleneck=bottleneck,
            small_experiment=small_experiment,
            capacity_tier=capacity_tier,
        ),
        _candidate_to_element(
            resource,
            bottleneck=bottleneck,
            small_experiment=small_experiment,
            capacity_tier=capacity_tier,
        ),
    ]

    effective_stage = stage or resolve_stage(decision_packet)
    catalog_candidate = _select_justified_catalog_candidate(
        catalog_source=catalog_source,
        bottleneck=bottleneck,
        stage=effective_stage,
    )
    if catalog_candidate is not None and len(elements) < MAX_STACK_ELEMENTS:
        elements.append(
            _candidate_to_element(
                catalog_candidate,
                bottleneck=bottleneck,
                small_experiment=small_experiment,
                capacity_tier=capacity_tier,
            )
        )

    opportunity_candidate = None
    if include_p1_lenses:
        opportunity_candidate = _select_justified_opportunity_candidate(
            opportunity_candidates or [],
            bottleneck=bottleneck,
        )
    if opportunity_candidate is not None and len(elements) < MAX_STACK_ELEMENTS:
        elements.append(
            _candidate_to_element(
                opportunity_candidate,
                bottleneck=bottleneck,
                small_experiment=small_experiment,
                capacity_tier=capacity_tier,
            )
        )

    elements = elements[:MAX_STACK_ELEMENTS]

    stack_key = run_id or decision_packet.userId
    hypothesis_id = f"hyp-{stack_key}"
    now = datetime.now(timezone.utc)

    return IdentityStack(
        id=f"stack-{stack_key}",
        userId=decision_packet.userId,
        hypothesisId=hypothesis_id,
        bottleneck=bottleneck,
        elements=elements,
        curatedAt=now,
    )


def assemble_stack(
    decision_packet: DecisionPacket,
    candidates: list[dict[str, Any]] | None = None,
    capacity_tier: str = "full",
    ledger_weights: dict[str, float] | None = None,
    *,
    run_id: str | None = None,
    llm: LLMProvider | None = None,
    search: SearchProvider | None = None,
    prior_stack: IdentityStack | None = None,
    knowledge_candidates: list[dict[str, Any]] | None = None,
    planner_candidates: list[dict[str, Any]] | None = None,
    small_experiment: bool = False,
    catalog_source: CatalogSource | None = None,
    stage: str | None = None,
    opportunity_candidates: list[dict[str, Any]] | None = None,
    include_p1_lenses: bool = False,
) -> IdentityStack:
    """Public assembler entry — used by graph assemble node and warm-cache seam."""
    _llm, _search = build_providers(llm, search)
    _ = (_llm, _search, candidates, ledger_weights)

    bottleneck = (
        decision_packet.bottleneck.bottleneck
        if decision_packet.bottleneck is not None
        else "execution"
    )
    if knowledge_candidates is None:
        raw = candidates or [get_fallback_knowledge(bottleneck)]
        knowledge_candidates = _normalize_knowledge_candidates(raw)
    if planner_candidates is None:
        planner_candidates = [get_fallback_mission(bottleneck, small_experiment=small_experiment)]

    return assemble_identity_stack(
        decision_packet,
        knowledge_candidates=knowledge_candidates,
        planner_candidates=planner_candidates,
        prior_stack=prior_stack,
        capacity_tier=capacity_tier,
        run_id=run_id,
        small_experiment=small_experiment,
        catalog_source=catalog_source,
        stage=stage,
        opportunity_candidates=opportunity_candidates,
        include_p1_lenses=include_p1_lenses,
    )
