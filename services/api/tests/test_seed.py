from __future__ import annotations

from app.core.config import get_settings
from app.models.intervention import InterventionModel
from app.models.calendar_event import CalendarEventModel
from app.models.identity_evolution import IdentityEvolutionProposalModel
from app.models.user import User
from app.repositories import evolution_repository, intervention_repository, ledger_repository
from app.workers.seed import (
    DEMO_HYPOTHESIS_FAMILY,
    _ensure_demo_dismissal_history,
    _ensure_demo_evolution_proposal,
    _ensure_prepared_intervention,
    _generate_history,
    _upsert_confirmed_twin,
    _upsert_demo_user,
)


def test_upsert_demo_user_is_idempotent(db_session) -> None:
    user_first = _upsert_demo_user(db_session)
    user_second = _upsert_demo_user(db_session)

    assert user_first.id == user_second.id == get_settings().demo_user_id
    assert db_session.query(User).filter_by(id=get_settings().demo_user_id).count() == 1


def test_generate_history_is_simulated_and_idempotent(db_session) -> None:
    user = _upsert_demo_user(db_session)

    inserted_first = _generate_history(db_session, user.id)
    assert inserted_first > 0

    # Re-running with the same fixed RNG seed must not duplicate rows —
    # every seeded event is idempotent via the same dedupe pipeline as live ingest.
    inserted_second = _generate_history(db_session, user.id)
    assert inserted_second == 0


def _clear_interventions(db_session, user_id: str) -> None:
    db_session.query(InterventionModel).filter(InterventionModel.user_id == user_id).delete()
    db_session.commit()


def test_ensure_prepared_intervention_is_idempotent(db_session) -> None:
    user = _upsert_demo_user(db_session)
    _upsert_confirmed_twin(db_session, user.id)
    _clear_interventions(db_session, user.id)

    created_first = _ensure_prepared_intervention(db_session, user.id)
    assert created_first is True
    assert intervention_repository.get_active(db_session, user.id) is not None

    created_second = _ensure_prepared_intervention(db_session, user.id)
    assert created_second is False


def test_ensure_demo_dismissal_history_seeds_two_and_is_idempotent(db_session) -> None:
    user = _upsert_demo_user(db_session)
    _upsert_confirmed_twin(db_session, user.id)
    _ensure_prepared_intervention(db_session, user.id)

    first = _ensure_demo_dismissal_history(db_session, user.id)
    assert first == 2
    assert ledger_repository.count_recent_dismissals(db_session, DEMO_HYPOTHESIS_FAMILY, 14) == 2

    second = _ensure_demo_dismissal_history(db_session, user.id)
    assert second == 0
    assert ledger_repository.count_recent_dismissals(db_session, DEMO_HYPOTHESIS_FAMILY, 14) == 2


def _clear_evolution_proposals(db_session, user_id: str) -> None:
    db_session.query(IdentityEvolutionProposalModel).filter(
        IdentityEvolutionProposalModel.user_id == user_id
    ).delete()
    db_session.commit()


def test_ensure_demo_evolution_proposal_is_idempotent(db_session) -> None:
    user = _upsert_demo_user(db_session)
    _upsert_confirmed_twin(db_session, user.id)
    _clear_evolution_proposals(db_session, user.id)

    first = _ensure_demo_evolution_proposal(db_session, user.id)
    assert first is True
    assert evolution_repository.has_pending_for_user(db_session, user.id) is True

    second = _ensure_demo_evolution_proposal(db_session, user.id)
    assert second is False


def _clear_calendar_events(db_session, user_id: str) -> None:
    db_session.query(CalendarEventModel).filter(CalendarEventModel.user_id == user_id).delete()
    db_session.commit()


def test_ensure_demo_calendar_events_is_idempotent(db_session) -> None:
    from app.repositories import calendar_repository
    from app.workers.seed import _ensure_demo_calendar_events

    user = _upsert_demo_user(db_session)
    _clear_calendar_events(db_session, user.id)
    first = _ensure_demo_calendar_events(db_session, user.id)
    assert first is True
    assert len(calendar_repository.list_upcoming(db_session, user.id)) == 3

    second = _ensure_demo_calendar_events(db_session, user.id)
    assert second is False
