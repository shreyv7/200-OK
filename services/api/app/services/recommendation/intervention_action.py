"""Public intervention-action seam for dismiss/complete paths — AIS M5/M6."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.schemas import IdentityStack, LedgerEntry
from app.schemas.ledger import LedgerAction
from app.services.recommendation.reflection_ledger import ReflectionResult, process_ledger_action


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
    result: ReflectionResult = process_ledger_action(
        user_id,
        hypothesis_id,
        hypothesis_family,
        action,
        timestamp=timestamp,
        failed_lens=failed_lens,
    )
    return InterventionOutcome(
        ledger_entry=result.ledger_entry,
        alternate_stack=result.alternate_stack,
        lens_weights=result.lens_weights,
    )
