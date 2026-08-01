from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.services.recommendation.ledger_intake import (
    clear_intake_store,
    evaluate_family_verdict,
    record_action,
)


def test_third_dismissal_within_window_fails() -> None:
    clear_intake_store()
    now = datetime.now(timezone.utc)
    for offset in (10, 5, 1):
        record_action(
            "user-aarav",
            "media-video",
            "dismissed",
            timestamp=now - timedelta(days=offset),
        )

    verdict = evaluate_family_verdict("user-aarav", "media-video", now=now)
    assert verdict.verdict == "failed"
    assert verdict.unlearning_triggered is True
    assert verdict.dismissal_count == 3


def test_third_dismissal_outside_window_stays_pending() -> None:
    clear_intake_store()
    now = datetime.now(timezone.utc)
    record_action(
        "user-aarav",
        "media-video",
        "dismissed",
        timestamp=now - timedelta(days=20),
    )
    record_action(
        "user-aarav",
        "media-video",
        "dismissed",
        timestamp=now - timedelta(days=15),
    )
    record_action(
        "user-aarav",
        "media-video",
        "dismissed",
        timestamp=now - timedelta(days=1),
    )

    verdict = evaluate_family_verdict("user-aarav", "media-video", now=now)
    assert verdict.verdict == "pending"
    assert verdict.unlearning_triggered is False
