from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.services.recommendation.intervention_action import on_intervention_action
from app.services.recommendation.ledger_intake import clear_intake_store
from app.services.recommendation.outcome_window import clear_outcome_store, record_delivery


def test_completion_marks_worked() -> None:
    clear_intake_store()
    clear_outcome_store()
    outcome = on_intervention_action(
        "user-aarav",
        "hyp-demo",
        "media-video",
        "completed",
    )
    assert outcome.ledger_entry.verdict == "worked"
    assert outcome.ledger_entry.unlearningTriggered is False


def test_delivered_without_completion_stays_pending() -> None:
    clear_intake_store()
    clear_outcome_store()
    now = datetime.now(timezone.utc)
    record_delivery("user-aarav", "media-video", timestamp=now - timedelta(days=1))
    outcome = on_intervention_action(
        "user-aarav",
        "hyp-demo",
        "media-video",
        "delivered",
        timestamp=now,
    )
    assert outcome.ledger_entry.verdict == "pending"
    assert "pending" in (outcome.ledger_entry.note or "").lower()
