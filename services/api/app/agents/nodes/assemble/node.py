"""Assemble Identity Stack from graph candidates — AIS M4/M6."""

from __future__ import annotations

from typing import Any

from app.schemas import DecisionPacket, IdentityStack
from app.services.recommendation.stack_assembler import assemble_identity_stack, resolve_stage


def assemble_node(state: dict[str, Any]) -> dict[str, Any]:
    packet = DecisionPacket.model_validate(state["decision_packet"])
    prior_stack = None
    if state.get("prior_stack"):
        prior_stack = IdentityStack.model_validate(state["prior_stack"])

    include_p1_lenses = bool(state.get("include_p1_lenses"))
    stack = assemble_identity_stack(
        packet,
        knowledge_candidates=list(state.get("knowledge_candidates") or []),
        planner_candidates=list(state.get("planner_candidates") or []),
        prior_stack=prior_stack,
        run_id=state.get("run_id"),
        small_experiment=bool(state.get("small_experiment")),
        catalog_source=state.get("catalog_source"),
        stage=state.get("stage") or resolve_stage(packet),
        opportunity_candidates=list(state.get("opportunity_candidates") or []),
        include_p1_lenses=include_p1_lenses,
    )

    return {
        "visited": ["assemble"],
        "identity_stack": stack.model_dump(),
    }
