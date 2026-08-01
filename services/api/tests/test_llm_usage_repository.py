"""B5 (docs/work.md): llm_usage_repository get_or_create/record_call
behavior, mirroring tests/test_budget_repository.py's shape."""

from __future__ import annotations

from datetime import date, timedelta

from app.models.user import User
from app.repositories import llm_usage_repository


def test_record_call_increments_count_and_tokens(db_session) -> None:
    user_id = "user-llm-usage-test"
    db_session.add(User(id=user_id, capacity=100.0))
    db_session.commit()

    row = llm_usage_repository.record_call(db_session, user_id, total_tokens=150)
    assert row.calls_today == 1
    assert row.tokens_today == 150
    assert row.last_call_at is not None

    row2 = llm_usage_repository.record_call(db_session, user_id, total_tokens=50)
    assert row2.calls_today == 2
    assert row2.tokens_today == 200


def test_record_call_with_no_token_count_defaults_to_zero(db_session) -> None:
    user_id = "user-llm-usage-test-2"
    db_session.add(User(id=user_id, capacity=100.0))
    db_session.commit()

    row = llm_usage_repository.record_call(db_session, user_id)
    assert row.calls_today == 1
    assert row.tokens_today == 0


def test_budget_resets_on_new_day(db_session) -> None:
    user_id = "user-llm-usage-test-3"
    db_session.add(User(id=user_id, capacity=100.0))
    db_session.commit()

    llm_usage_repository.record_call(db_session, user_id, total_tokens=100)
    row = llm_usage_repository.get_or_create(db_session, user_id)
    row.budget_date = date.today() - timedelta(days=1)
    db_session.commit()

    refreshed = llm_usage_repository.get_or_create(db_session, user_id)
    assert refreshed.calls_today == 0
    assert refreshed.tokens_today == 0
    assert refreshed.budget_date == date.today()
