"""Production Guardian gate — capacity/budget context + pre-delivery enforcement."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.repositories import budget_repository, ledger_repository, user_repository
from app.schemas import IdentityStack
from app.schemas.stack import InterventionVariant
from app.services.recommendation.guardian import GuardianContext, GuardianDecision, evaluate_guardian
from app.services.recommendation.variants import generate_variants, select_variant_by_intensity


def _as_utc(value: datetime) -> datetime:
    """Normalize naive/aware timestamps so comparisons never raise TypeError."""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def recent_dismissal_rate(db: Session, user_id: str, *, window_days: int = 14) -> float:
    cutoff = datetime.now(timezone.utc) - timedelta(days=window_days)
    entries = ledger_repository.list_for_user(db, user_id)
    recent = [entry for entry in entries if _as_utc(entry.timestamp) >= cutoff]
    if not recent:
        return 0.0
    dismissals = sum(1 for entry in recent if entry.action == "dismissed")
    return dismissals / len(recent)


def build_guardian_context(db: Session, user_id: str) -> GuardianContext:
    user = user_repository.get_by_id(db, user_id)
    budget = budget_repository.get_or_create(db, user_id)
    return GuardianContext(
        capacity_pct=int(user.capacity) if user is not None else 100,
        interventions_today=budget.interventions_today,
        last_intervention_at=budget.last_intervention_at,
        recent_dismissal_rate=recent_dismissal_rate(db, user_id),
    )


def guardian_context_from_state(state: dict[str, Any]) -> GuardianContext:
    last_at = state.get("last_intervention_at")
    if isinstance(last_at, str):
        last_at = datetime.fromisoformat(last_at.replace("Z", "+00:00"))
    return GuardianContext(
        capacity_pct=int(state.get("capacity_pct", 100)),
        interventions_today=int(state.get("interventions_today", 0)),
        last_intervention_at=last_at,
        recent_dismissal_rate=float(state.get("recent_dismissal_rate", 0.0)),
    )


def guardian_decision_to_dict(decision: GuardianDecision) -> dict[str, Any]:
    return {
        "action": decision.action,
        "intensity": decision.intensity,
        "reason_code": decision.reason_code,
        "reason": decision.reason,
    }


@dataclass
class GuardianGateResult:
    decision: GuardianDecision
    variants: list[InterventionVariant]
    stack: IdentityStack | None
    delivery_allowed: bool


def apply_guardian_gate(stack: IdentityStack, context: GuardianContext) -> GuardianGateResult:
    variants = generate_variants(stack)
    decision = evaluate_guardian(context)

    if decision.action in {"cancel", "delay"}:
        return GuardianGateResult(
            decision=decision,
            variants=variants,
            stack=None,
            delivery_allowed=False,
        )

    selected = select_variant_by_intensity(variants, decision.intensity)
    return GuardianGateResult(
        decision=decision,
        variants=variants,
        stack=selected.stack,
        delivery_allowed=True,
    )


def record_guardian_delivery(db: Session, user_id: str) -> None:
    """Increment intervention budget after a stack clears the Guardian gate."""
    budget_repository.record_intervention_delivered(db, user_id)
