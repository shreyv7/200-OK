from __future__ import annotations

from datetime import datetime

from app.repositories import twin_repository
from app.services.recommendation.evolution_hook import on_evolution_accepted
from app.services.recommendation.stack_state import clear_stack_state
from app.workers.seed import _DECLARED_ATTRIBUTES
from tests.conftest import ensure_user
from tests.fixtures.sample_data import sample_evolution_accepted_event


def test_evolution_accept_run_id_carries_declared_self_version(db_session) -> None:
    clear_stack_state()
    ensure_user(db_session, "user-aarav")
    if twin_repository.get_active_declared_self(db_session, "user-aarav") is None:
        twin_repository.create_version(
            db_session,
            user_id="user-aarav",
            version=1,
            attributes=_DECLARED_ATTRIBUTES,
            confirmed_at=datetime.utcnow(),
        )

    event = sample_evolution_accepted_event(
        with_gap_snapshot=True,
        declared_self_version=5,
    )

    result = on_evolution_accepted(event, db=db_session)

    assert result["declaredSelfVersion"] == 5
    assert result["run_id"] == "evolve-user-aarav-v5"
    assert result["identity_stack"] is not None
    assert result["identity_stack"]["id"] == "stack-evolve-user-aarav-v5"
