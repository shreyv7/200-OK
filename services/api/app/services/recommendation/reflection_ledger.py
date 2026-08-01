"""Production Trust Ledger reflection — verdict rules, persistence, and unlearning."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy.orm import Session

from app.repositories import intervention_repository, ledger_repository
from app.schemas import IdentityStack, LedgerEntry
from app.schemas.ledger import LedgerAction, LedgerVerdict
from app.services.identity.scoring.constants import (
    DISMISSAL_FAILURE_THRESHOLD,
    DISMISSAL_WINDOW_DAYS,
)
from app.services.recommendation.alternate_lens import request_alternate_stack
from app.services.recommendation.lens_weights import apply_unlearning, get_lens_weights, set_lens_weights
from app.services.recommendation.ledger_intake import record_action, record_evidence_ids
from app.services.recommendation.outcome_window import evaluate_intervention_verdict
from app.services.recommendation.stack_state import get_active_stack, set_active_stack
from app.services.recommendation.variants import generate_variants

UNLEARNING_LENS_ADJUSTMENT: dict[str, float] = {"media": -0.4}


@dataclass
class ReflectionResult:
    ledger_entry: LedgerEntry
    alternate_stack: IdentityStack | None = None
    lens_weights: dict[str, float] | None = None


def attach_evidence(hypothesis_id: str, evidence_ids: list[str]) -> None:
    record_evidence_ids(hypothesis_id, evidence_ids)


def _dismissal_trips_failure(
    db: Session | None,
    user_id: str,
    hypothesis_family: str,
) -> bool:
    if db is not None:
        dismissal_count = ledger_repository.count_recent_dismissals(
            db, user_id, hypothesis_family, DISMISSAL_WINDOW_DAYS
        )
        return dismissal_count + 1 >= DISMISSAL_FAILURE_THRESHOLD

    from app.services.recommendation.ledger_intake import evaluate_family_verdict

    return evaluate_family_verdict(user_id, hypothesis_family).unlearning_triggered


def _persist_alternate_stack(db: Session, user_id: str, stack: IdentityStack) -> None:
    variants = {
        variant.intensity: variant.model_dump(mode="json")
        for variant in generate_variants(stack)
    }
    intervention_repository.create(db, user_id, stack, variants=variants)


def process_ledger_action(
    user_id: str,
    hypothesis_id: str,
    hypothesis_family: str,
    action: LedgerAction,
    *,
    db: Session | None = None,
    timestamp: datetime | None = None,
    failed_lens: str = "media",
) -> ReflectionResult:
    """Single production path for intervention dismiss/complete/deliver actions."""
    when = timestamp or datetime.now(timezone.utc)
    record_action(user_id, hypothesis_family, action, timestamp=when)

    verdict: LedgerVerdict = "pending"
    unlearning = False
    lens_adjustment: dict[str, float] | None = None
    note: str | None = None
    alternate_stack: IdentityStack | None = None
    lens_weights: dict[str, float] | None = None

    if action == "dismissed":
        if _dismissal_trips_failure(db, user_id, hypothesis_family):
            verdict = "failed"
            unlearning = True
            lens_adjustment = UNLEARNING_LENS_ADJUSTMENT
        else:
            verdict = "pending"
    elif action == "completed":
        evaluate_intervention_verdict(user_id, hypothesis_family, action, now=when)
        verdict = "worked"
        note = "Hypothesis worked based on completion evidence in the outcome window."
    else:
        outcome = evaluate_intervention_verdict(
            user_id, hypothesis_family, action, now=when
        )
        verdict = outcome.verdict
        if action == "delivered":
            note = "Outcome window open; verdict pending."

    if unlearning:
        weights = get_lens_weights(user_id)
        weights, _adjustment = apply_unlearning(weights, failed_lens=failed_lens)
        set_lens_weights(user_id, weights)
        lens_weights = weights
        note = f"System Unlearning: {failed_lens.title()} −40%; switched to Micro-Action"
        alternate_stack = request_alternate_stack(
            user_id=user_id,
            prior_stack=get_active_stack(user_id),
            failed_lens=failed_lens,
            hypothesis_id=hypothesis_id,
        )
        set_active_stack(user_id, alternate_stack)
        if db is not None:
            _persist_alternate_stack(db, user_id, alternate_stack)

    if db is not None:
        entry = ledger_repository.record(
            db,
            user_id=user_id,
            hypothesis_id=hypothesis_id,
            hypothesis_family=hypothesis_family,
            action=action,
            verdict=verdict,
            unlearning_triggered=unlearning,
            lens_weight_adjustment=lens_adjustment,
            note=note,
            timestamp=when,
        )
    else:
        entry = LedgerEntry(
            id=f"ledger-{uuid4().hex[:12]}",
            userId=user_id,
            hypothesisId=hypothesis_id,
            hypothesisFamily=hypothesis_family,
            action=action,
            verdict=verdict,
            timestamp=when,
            unlearningTriggered=unlearning,
            lensWeightAdjustment=lens_adjustment,
            note=note,
        )

    return ReflectionResult(
        ledger_entry=entry,
        alternate_stack=alternate_stack,
        lens_weights=lens_weights,
    )
