"""Guardian pre-delivery gate — AIS M5."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from app.schemas import IdentityStack
from app.services.recommendation.guardian import GuardianContext, GuardianDecision, evaluate_guardian
from app.services.recommendation.variants import generate_variants, select_variant_by_intensity


def _decision_to_dict(decision: GuardianDecision) -> dict[str, Any]:
    return {
        "action": decision.action,
        "intensity": decision.intensity,
        "reason_code": decision.reason_code,
        "reason": decision.reason,
    }


def _parse_context(state: dict[str, Any]) -> GuardianContext:
    last_at = state.get("last_intervention_at")
    if isinstance(last_at, str):
        last_at = datetime.fromisoformat(last_at.replace("Z", "+00:00"))
    return GuardianContext(
        capacity_pct=int(state.get("capacity_pct", 100)),
        interventions_today=int(state.get("interventions_today", 0)),
        last_intervention_at=last_at,
        recent_dismissal_rate=float(state.get("recent_dismissal_rate", 0.0)),
    )


def guardian_node(state: dict[str, Any]) -> dict[str, Any]:
    stack_data = state.get("identity_stack")
    if not stack_data:
        return {"visited": ["guardian"], "delivery_allowed": False}

    stack = IdentityStack.model_validate(stack_data)
    variants = generate_variants(stack)
    decision = evaluate_guardian(_parse_context(state))

    if decision.action in {"cancel", "delay"}:
        return {
            "visited": ["guardian"],
            "guardian_decision": _decision_to_dict(decision),
            "intervention_variants": [variant.model_dump() for variant in variants],
            "delivery_allowed": False,
        }

    selected = select_variant_by_intensity(variants, decision.intensity)
    return {
        "visited": ["guardian"],
        "guardian_decision": _decision_to_dict(decision),
        "intervention_variants": [variant.model_dump() for variant in variants],
        "identity_stack": selected.stack.model_dump(),
        "delivery_allowed": True,
    }
