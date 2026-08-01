from __future__ import annotations

from app.services.recommendation.onboarding_hook import (
    build_onboarding_decision_packet,
    emit_onboarding_confirmed,
    on_onboarding_confirmed,
)
from app.services.recommendation.stack_state import clear_stack_state, get_active_stack
from tests.fixtures.sample_data import sample_onboarding_confirm_event


def test_onboarding_confirm_schedules_coordinator_with_gap_snapshot() -> None:
    clear_stack_state()
    event = sample_onboarding_confirm_event(with_gap_snapshot=True)

    result = on_onboarding_confirmed(event)

    assert "coordinator" in result["visited"]
    assert result["trigger"] == "onboarding.confirmed"
    packet = result["decision_packet"]
    assert packet["gapDelta"] == 6.0
    assert packet["invalidateStack"] is True
    assert result["stack_draft"]["invalidate"] is True


def test_onboarding_confirm_without_snapshot_uses_degraded_invalidate() -> None:
    clear_stack_state()
    event = sample_onboarding_confirm_event(with_gap_snapshot=False)

    result = on_onboarding_confirmed(event)

    assert result["decision_packet"]["gapDelta"] == 0.0
    assert result["decision_packet"]["invalidateStack"] is True
    assert result["stack_draft"]["invalidate"] is True


def test_emit_onboarding_confirmed_warms_cache_best_effort() -> None:
    clear_stack_state()
    event = sample_onboarding_confirm_event(with_gap_snapshot=False)

    result = emit_onboarding_confirmed(event)

    assert result["warm_cache"]["ok"] is True
    assert get_active_stack(event.userId) is not None


def test_build_onboarding_decision_packet_forces_invalidate() -> None:
    event = sample_onboarding_confirm_event(with_gap_snapshot=True, twin_version=2)
    packet = build_onboarding_decision_packet(event)
    assert packet.invalidateStack is True
