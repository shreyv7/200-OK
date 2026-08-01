"""Trust Ledger intake + dismissal-window verdict rules — AIS M5."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from app.schemas.ledger import LedgerAction, LedgerVerdict
from app.services.identity.scoring.constants import (
    DISMISSAL_FAILURE_THRESHOLD,
    DISMISSAL_WINDOW_DAYS,
)

_intake_store: dict[str, list[tuple[str, datetime]]] = {}
_action_store: dict[str, list[tuple[LedgerAction, datetime]]] = {}


def _family_key(user_id: str, hypothesis_family: str) -> str:
    return f"{user_id}:{hypothesis_family}"


def record_evidence_ids(hypothesis_id: str, evidence_ids: list[str]) -> None:
    """Associate evidence IDs with a hypothesis for a future outcome window."""
    if not evidence_ids:
        return
    now = datetime.now(timezone.utc)
    entries = _intake_store.setdefault(hypothesis_id, [])
    for evidence_id in evidence_ids:
        if evidence_id:
            entries.append((evidence_id, now))


def record_action(
    user_id: str,
    hypothesis_family: str,
    action: LedgerAction,
    *,
    timestamp: datetime | None = None,
) -> None:
    """Record a ledger action for failure-threshold evaluation."""
    when = timestamp or datetime.now(timezone.utc)
    key = _family_key(user_id, hypothesis_family)
    _action_store.setdefault(key, []).append((action, when))


def get_pending_window(hypothesis_id: str) -> list[str]:
    """Return evidence IDs recorded for the hypothesis (deduped, insertion order)."""
    seen: set[str] = set()
    ordered: list[str] = []
    for evidence_id, _ in _intake_store.get(hypothesis_id, []):
        if evidence_id not in seen:
            seen.add(evidence_id)
            ordered.append(evidence_id)
    return ordered


@dataclass
class VerdictResult:
    verdict: LedgerVerdict
    unlearning_triggered: bool
    dismissal_count: int


def evaluate_family_verdict(
    user_id: str,
    hypothesis_family: str,
    *,
    now: datetime | None = None,
) -> VerdictResult:
    """3 dismissals within 14 days → failed (deterministic)."""
    when = now or datetime.now(timezone.utc)
    cutoff = when - timedelta(days=DISMISSAL_WINDOW_DAYS)
    key = _family_key(user_id, hypothesis_family)
    actions = _action_store.get(key, [])

    dismissal_count = sum(
        1 for action, ts in actions if action == "dismissed" and ts >= cutoff
    )
    failed = dismissal_count >= DISMISSAL_FAILURE_THRESHOLD
    return VerdictResult(
        verdict="failed" if failed else "pending",
        unlearning_triggered=failed,
        dismissal_count=dismissal_count,
    )


def clear_intake_store() -> None:
    """Test helper — reset in-memory intake."""
    _intake_store.clear()
    _action_store.clear()
