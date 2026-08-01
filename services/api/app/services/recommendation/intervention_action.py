"""Public intervention-action seam for Backend dismiss/complete paths — AIS M5."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from app.schemas import IdentityStack, LedgerEntry
from app.schemas.ledger import LedgerAction
from app.services.recommendation.alternate_lens import request_alternate_stack
from app.services.recommendation.lens_weights import apply_unlearning, get_lens_weights, set_lens_weights
from app.services.recommendation.ledger_intake import evaluate_family_verdict, record_action
from app.services.recommendation.stack_state import get_active_stack, set_active_stack


@dataclass
class InterventionOutcome:
    ledger_entry: LedgerEntry
    alternate_stack: IdentityStack | None = None
    lens_weights: dict[str, float] | None = None


def on_intervention_action(
    user_id: str,
    hypothesis_id: str,
    hypothesis_family: str,
    action: LedgerAction,
    *,
    timestamp: datetime | None = None,
    failed_lens: str = "media",
) -> InterventionOutcome:
    """Tier-0 deterministic path for dismiss/complete logging (<250ms when Backend persists)."""
    when = timestamp or datetime.now(timezone.utc)
    record_action(user_id, hypothesis_family, action, timestamp=when)

    verdict = evaluate_family_verdict(user_id, hypothesis_family, now=when)
    weights = get_lens_weights(user_id)
    adjustment = None
    note = None
    alternate_stack = None

    if verdict.unlearning_triggered:
        weights, adjustment = apply_unlearning(weights, failed_lens=failed_lens)
        set_lens_weights(user_id, weights)
        note = f"System Unlearning: {failed_lens.title()} −40%; switched to Micro-Action"
        alternate_stack = request_alternate_stack(
            user_id=user_id,
            prior_stack=get_active_stack(user_id),
            failed_lens=failed_lens,
            hypothesis_id=hypothesis_id,
        )
        set_active_stack(user_id, alternate_stack)

    entry = LedgerEntry(
        id=f"ledger-{uuid4().hex[:12]}",
        userId=user_id,
        hypothesisId=hypothesis_id,
        hypothesisFamily=hypothesis_family,
        action=action,
        verdict=verdict.verdict,
        timestamp=when,
        unlearningTriggered=verdict.unlearning_triggered,
        lensWeightAdjustment=adjustment,
        note=note,
    )
    return InterventionOutcome(
        ledger_entry=entry,
        alternate_stack=alternate_stack,
        lens_weights=weights if verdict.unlearning_triggered else None,
    )
