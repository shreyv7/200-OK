from __future__ import annotations

from datetime import datetime

from app.repositories import intervention_repository
from app.services.recommendation.evolution_hook import (
    build_evolution_decision_packet,
    emit_evolution_accepted,
    on_evolution_accepted,
)
from app.services.recommendation.stack_state import clear_stack_state, get_active_stack, get_active_stack_flags, set_active_stack
from app.workers.seed import _DECLARED_ATTRIBUTES
from tests.conftest import ensure_user
from tests.fixtures.sample_data import sample_evolution_accepted_event, sample_identity_stack
from app.repositories import twin_repository


def _ensure_demo_twin(db_session, user_id: str = "user-aarav") -> None:
    ensure_user(db_session, user_id)
    if twin_repository.get_active_declared_self(db_session, user_id) is None:
        twin_repository.create_version(
            db_session,
            user_id=user_id,
            version=1,
            attributes=_DECLARED_ATTRIBUTES,
            confirmed_at=datetime.utcnow(),
        )


def test_evolution_accept_forces_invalidate_and_recuration(db_session) -> None:
    clear_stack_state()
    _ensure_demo_twin(db_session)
    event = sample_evolution_accepted_event(with_gap_snapshot=True)

    result = on_evolution_accepted(event, db=db_session)

    assert result["trigger"] == "evolution.accepted"
    assert result["decision_packet"]["invalidateStack"] is True
    assert result["identity_stack"] is not None
    assert len(result["identity_stack"]["elements"]) >= 2
    flags = get_active_stack_flags(event.userId)
    assert flags.hasActiveStack is True
    assert get_active_stack(event.userId) is not None
    assert intervention_repository.get_active(db_session, event.userId) is not None


def test_emit_evolution_accepted_warms_cache_best_effort(db_session) -> None:
    clear_stack_state()
    _ensure_demo_twin(db_session)
    event = sample_evolution_accepted_event(with_gap_snapshot=False, declared_self_version=3)

    result = emit_evolution_accepted(event, db=db_session)

    assert result["warm_cache"]["ok"] is True
    assert result["warm_cache"]["stackId"] is not None


def test_build_evolution_decision_packet_forces_invalidate() -> None:
    clear_stack_state()
    event = sample_evolution_accepted_event(with_gap_snapshot=True, declared_self_version=4)
    packet = build_evolution_decision_packet(event)
    assert packet.invalidateStack is True


def test_evolution_accept_replaces_prior_stack(db_session) -> None:
    clear_stack_state()
    _ensure_demo_twin(db_session)
    prior = sample_identity_stack()
    set_active_stack("user-aarav", prior)
    event = sample_evolution_accepted_event(with_gap_snapshot=True, declared_self_version=2)

    on_evolution_accepted(event, db=db_session)

    refreshed = get_active_stack("user-aarav")
    assert refreshed is not None
    assert refreshed.id != prior.id
