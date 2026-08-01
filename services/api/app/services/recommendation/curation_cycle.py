"""Public curation cycle seam for Backend refresh/Celery — AIS M4/M5."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.agents.graphs.coordinator import build_coordinator_graph
from app.providers.llm.base import LLMProvider
from app.providers.search.base import SearchProvider
from app.schemas import DecisionPacket, IdentityStack, InterventionVariant
from app.services.recommendation.curation_context import curation_providers
from app.services.recommendation.catalog import CatalogSource
from app.services.recommendation.guardian import GuardianContext
from app.services.recommendation.stack_assembler import resolve_stage
from app.services.recommendation.stack_state import get_active_stack, set_active_stack
from app.services.recommendation.variants import generate_variants, select_variant_by_capacity


@dataclass
class CurationCycleResult:
    stack: IdentityStack
    variants: list[InterventionVariant]
    guardian_decision: dict[str, Any] | None = None
    delivery_allowed: bool = True


def _build_initial_state(
    decision_packet: DecisionPacket,
    *,
    trigger: str,
    run_id: str,
    prior_stack: IdentityStack | None = None,
    search_provider: SearchProvider | None = None,
    llm_provider: LLMProvider | None = None,
    guardian_context: GuardianContext | None = None,
    catalog_source: CatalogSource | None = None,
    include_p1_lenses: bool = False,
    stage: str | None = None,
) -> dict[str, Any]:
    state: dict[str, Any] = {
        "trigger": trigger,
        "run_id": run_id,
        "user_id": decision_packet.userId,
        "decision_packet": decision_packet.model_dump(),
        "stack_draft": None,
        "visited": [],
        "evidence_id": None,
        "hypothesis_id": f"hyp-{run_id}",
    }
    if prior_stack is not None:
        state["prior_stack"] = prior_stack.model_dump()
    if search_provider is not None:
        state["search_provider"] = search_provider
    if llm_provider is not None:
        state["llm_provider"] = llm_provider
    if guardian_context is not None:
        state["capacity_pct"] = guardian_context.capacity_pct
        state["interventions_today"] = guardian_context.interventions_today
        state["last_intervention_at"] = guardian_context.last_intervention_at
        state["recent_dismissal_rate"] = guardian_context.recent_dismissal_rate
    if catalog_source is not None:
        state["catalog_source"] = catalog_source
    if include_p1_lenses:
        state["include_p1_lenses"] = True
        state["stage"] = stage or resolve_stage(decision_packet)
    return state


def run_curation_cycle(
    decision_packet: DecisionPacket,
    *,
    trigger: str = "stack.refresh",
    run_id: str | None = None,
    prior_stack: IdentityStack | None = None,
    search: SearchProvider | None = None,
    llm: LLMProvider | None = None,
    persist_active_stack: bool = True,
    guardian_context: GuardianContext | None = None,
    with_variants: bool = False,
    catalog_source: CatalogSource | None = None,
    include_p1_lenses: bool = False,
    stage: str | None = None,
) -> IdentityStack | CurationCycleResult:
    """Decision → diagnose → retrieve → assemble → guardian; never empty stack."""
    effective_run_id = run_id or f"curation-{decision_packet.userId}"
    if prior_stack is None:
        prior_stack = get_active_stack(decision_packet.userId)

    state = _build_initial_state(
        decision_packet,
        trigger=trigger,
        run_id=effective_run_id,
        prior_stack=prior_stack,
        search_provider=search,
        llm_provider=llm,
        guardian_context=guardian_context,
        catalog_source=catalog_source,
        include_p1_lenses=include_p1_lenses,
        stage=stage,
    )

    graph = build_coordinator_graph()
    with curation_providers(llm=llm, search=search):
        result = graph.invoke(state)

    stack_data = result.get("identity_stack")
    if stack_data is None:
        from app.services.recommendation.stack_assembler import assemble_stack

        stack = assemble_stack(
            decision_packet,
            run_id=effective_run_id,
            prior_stack=prior_stack,
            llm=llm,
            search=search,
            small_experiment=bool(result.get("small_experiment")),
        )
        variants = generate_variants(stack) if with_variants else []
        if guardian_context is not None:
            stack = select_variant_by_capacity(variants, guardian_context.capacity_pct).stack
    else:
        stack = IdentityStack.model_validate(stack_data)
        variant_payloads = result.get("intervention_variants") or []
        variants = [InterventionVariant.model_validate(item) for item in variant_payloads]
        if not variants and with_variants:
            variants = generate_variants(stack)

    if persist_active_stack and result.get("delivery_allowed", True):
        set_active_stack(decision_packet.userId, stack)

    if with_variants or guardian_context is not None:
        return CurationCycleResult(
            stack=stack,
            variants=variants,
            guardian_decision=result.get("guardian_decision"),
            delivery_allowed=bool(result.get("delivery_allowed", True)),
        )

    return stack
