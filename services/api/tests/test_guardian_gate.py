from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.services.recommendation.guardian import GuardianContext, evaluate_guardian


def test_daily_cap_cancels_delivery() -> None:
    decision = evaluate_guardian(
        GuardianContext(capacity_pct=100, interventions_today=5)
    )
    assert decision.action == "cancel"
    assert decision.reason_code == "daily_cap"


def test_low_capacity_downgrades_to_micro() -> None:
    decision = evaluate_guardian(GuardianContext(capacity_pct=20))
    assert decision.action == "downgrade"
    assert decision.intensity == "micro"
    assert "Capacity changed" in decision.reason


def test_too_soon_delays_delivery() -> None:
    now = datetime.now(timezone.utc)
    decision = evaluate_guardian(
        GuardianContext(
            capacity_pct=100,
            last_intervention_at=now - timedelta(minutes=5),
            now=now,
        )
    )
    assert decision.action == "delay"
    assert decision.reason_code == "too_soon"


def test_healthy_context_delivers_full() -> None:
    decision = evaluate_guardian(GuardianContext(capacity_pct=90))
    assert decision.action == "deliver"
    assert decision.intensity == "full"
