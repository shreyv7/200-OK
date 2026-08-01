from __future__ import annotations

from app.repositories import budget_repository


def test_record_intervention_delivered_increments_count(db_session) -> None:
    user_id = "user-budget-test"
    budget_repository.get_or_create(db_session, user_id)

    row = budget_repository.record_intervention_delivered(db_session, user_id)
    assert row.interventions_today == 1
    assert row.last_intervention_at is not None

    row2 = budget_repository.record_intervention_delivered(db_session, user_id)
    assert row2.interventions_today == 2
