"""Trust Ledger outcome windows — success/pending paths — AIS M6."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from app.schemas.ledger import LedgerAction, LedgerVerdict
from app.services.recommendation.ledger_intake import VerdictResult, evaluate_family_verdict

OUTCOME_WINDOW_DAYS = 7

_delivery_store: dict[str, datetime] = {}
_completion_store: dict[str, list[datetime]] = {}


def _family_key(user_id: str, hypothesis_family: str) -> str:
    return f"{user_id}:{hypothesis_family}"


def record_delivery(
    user_id: str,
    hypothesis_family: str,
    *,
    timestamp: datetime | None = None,
) -> None:
    when = timestamp or datetime.now(timezone.utc)
    _delivery_store[_family_key(user_id, hypothesis_family)] = when


def record_completion(
    user_id: str,
    hypothesis_family: str,
    *,
    timestamp: datetime | None = None,
) -> None:
    when = timestamp or datetime.now(timezone.utc)
    key = _family_key(user_id, hypothesis_family)
    _completion_store.setdefault(key, []).append(when)


def has_open_outcome_window(
    user_id: str,
    hypothesis_family: str,
    *,
    now: datetime | None = None,
) -> bool:
    when = now or datetime.now(timezone.utc)
    key = _family_key(user_id, hypothesis_family)
    delivered_at = _delivery_store.get(key)
    if delivered_at is None:
        return False
    if delivered_at < when - timedelta(days=OUTCOME_WINDOW_DAYS):
        return False
    completions = [ts for ts in _completion_store.get(key, []) if ts >= delivered_at]
    return len(completions) == 0


def evaluate_intervention_verdict(
    user_id: str,
    hypothesis_family: str,
    action: LedgerAction,
    *,
    now: datetime | None = None,
) -> VerdictResult:
    """Combine M5 failure rule with P1 worked/pending outcome windows."""
    when = now or datetime.now(timezone.utc)
    failure = evaluate_family_verdict(user_id, hypothesis_family, now=when)
    if failure.unlearning_triggered:
        return failure

    if action == "completed":
        record_completion(user_id, hypothesis_family, timestamp=when)
        return VerdictResult(
            verdict="worked",
            unlearning_triggered=False,
            dismissal_count=failure.dismissal_count,
        )

    if action == "delivered":
        record_delivery(user_id, hypothesis_family, timestamp=when)

    if has_open_outcome_window(user_id, hypothesis_family, now=when):
        return VerdictResult(
            verdict="pending",
            unlearning_triggered=False,
            dismissal_count=failure.dismissal_count,
        )

    return VerdictResult(
        verdict="pending",
        unlearning_triggered=False,
        dismissal_count=failure.dismissal_count,
    )


def clear_outcome_store() -> None:
    """Test helper."""
    _delivery_store.clear()
    _completion_store.clear()
