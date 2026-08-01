from __future__ import annotations

from app.core.config import get_settings
from app.models.user import User
from app.repositories import intervention_repository
from app.workers.seed import (
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


def test_ensure_prepared_intervention_is_idempotent(db_session) -> None:
    user = _upsert_demo_user(db_session)
    _upsert_confirmed_twin(db_session, user.id)

    created_first = _ensure_prepared_intervention(db_session, user.id)
    assert created_first is True
    assert intervention_repository.get_active(db_session, user.id) is not None

    created_second = _ensure_prepared_intervention(db_session, user.id)
    assert created_second is False
