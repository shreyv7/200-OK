"""Assemble Identity Stack from graph candidates — AIS M4."""

from __future__ import annotations

from typing import Any

from app.schemas import DecisionPacket, IdentityStack
from app.services.recommendation.stack_assembler import assemble_identity_stack


def assemble_node(state: dict[str, Any]) -> dict[str, Any]:
    packet = DecisionPacket.model_validate(state["decision_packet"])
    prior_stack = None
    if state.get("prior_stack"):
        prior_stack = IdentityStack.model_validate(state["prior_stack"])

    stack = assemble_identity_stack(
        packet,
        knowledge_candidates=list(state.get("knowledge_candidates") or []),
        planner_candidates=list(state.get("planner_candidates") or []),
        prior_stack=prior_stack,
        run_id=state.get("run_id"),
        small_experiment=bool(state.get("small_experiment")),
    )

    return {
        "visited": ["assemble"],
        "identity_stack": stack.model_dump(),
    }
