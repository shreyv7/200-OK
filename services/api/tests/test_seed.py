from __future__ import annotations

from app.core.config import get_settings
from app.models.user import User
from app.workers.seed import _generate_history, _upsert_demo_user


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
