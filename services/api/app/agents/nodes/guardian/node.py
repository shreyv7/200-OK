"""Guardian pre-delivery gate — AIS M5."""

from __future__ import annotations

from typing import Any

from app.schemas import IdentityStack
from app.services.recommendation.guardian_gate import (
    apply_guardian_gate,
    guardian_context_from_state,
    guardian_decision_to_dict,
)


def guardian_node(state: dict[str, Any]) -> dict[str, Any]:
    stack_data = state.get("identity_stack")
    if not stack_data:
        return {"visited": ["guardian"], "delivery_allowed": False}

    stack = IdentityStack.model_validate(stack_data)
    result = apply_guardian_gate(stack, guardian_context_from_state(state))

    payload: dict[str, Any] = {
        "visited": ["guardian"],
        "guardian_decision": guardian_decision_to_dict(result.decision),
        "intervention_variants": [variant.model_dump() for variant in result.variants],
        "delivery_allowed": result.delivery_allowed,
    }
    if result.stack is not None:
        payload["identity_stack"] = result.stack.model_dump()
    return payload
