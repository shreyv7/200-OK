from __future__ import annotations

from app.services.recommendation.evolution_hook import (
    build_evolution_decision_packet,
    emit_evolution_accepted,
    on_evolution_accepted,
)
from app.services.recommendation.stack_state import clear_stack_state, get_active_stack, get_active_stack_flags
from tests.fixtures.sample_data import sample_evolution_accepted_event, sample_identity_stack


def test_evolution_accept_forces_invalidate_and_recuration() -> None:
    clear_stack_state()
    event = sample_evolution_accepted_event(with_gap_snapshot=True)

    result = on_evolution_accepted(event)

    assert result["trigger"] == "evolution.accepted"
    assert result["decision_packet"]["invalidateStack"] is True
    assert result["identity_stack"] is not None
    assert len(result["identity_stack"]["elements"]) >= 2
    flags = get_active_stack_flags(event.userId)
    assert flags.hasActiveStack is True
    assert get_active_stack(event.userId) is not None


def test_emit_evolution_accepted_warms_cache_best_effort() -> None:
    clear_stack_state()
    event = sample_evolution_accepted_event(with_gap_snapshot=False, declared_self_version=3)

    result = emit_evolution_accepted(event)

    assert result["warm_cache"]["ok"] is True
    assert result["warm_cache"]["stackId"] is not None


def test_build_evolution_decision_packet_forces_invalidate() -> None:
    clear_stack_state()
    event = sample_evolution_accepted_event(with_gap_snapshot=True, declared_self_version=4)
    packet = build_evolution_decision_packet(event)
    assert packet.invalidateStack is True


def test_evolution_accept_replaces_prior_stack() -> None:
    clear_stack_state()
    prior = sample_identity_stack()
    from app.services.recommendation.stack_state import set_active_stack

    set_active_stack("user-aarav", prior)
    event = sample_evolution_accepted_event(with_gap_snapshot=True, declared_self_version=2)

    result = on_evolution_accepted(event)

    refreshed = get_active_stack("user-aarav")
    assert refreshed is not None
    assert refreshed.id != prior.id
