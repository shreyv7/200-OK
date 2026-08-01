"""Public curation cycle seam for Backend refresh/Celery — AIS M4."""

from __future__ import annotations

from typing import Any

from app.agents.graphs.coordinator import build_coordinator_graph
from app.providers.llm.base import LLMProvider
from app.providers.search.base import SearchProvider
from app.schemas import DecisionPacket, IdentityStack
from app.services.recommendation.curation_context import curation_providers
from app.services.recommendation.stack_state import get_active_stack, set_active_stack


def _build_initial_state(
    decision_packet: DecisionPacket,
    *,
    trigger: str,
    run_id: str,
    prior_stack: IdentityStack | None = None,
    search_provider: SearchProvider | None = None,
    llm_provider: LLMProvider | None = None,
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
) -> IdentityStack:
    """Decision → diagnose → retrieve → assemble; never returns an empty stack."""
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
    else:
        stack = IdentityStack.model_validate(stack_data)

    if persist_active_stack:
        set_active_stack(decision_packet.userId, stack)
    return stack
