from __future__ import annotations

from app.services.recommendation.evolution_hook import on_evolution_accepted
from app.services.recommendation.stack_state import clear_stack_state
from tests.fixtures.sample_data import sample_evolution_accepted_event


def test_evolution_accept_run_id_carries_declared_self_version() -> None:
    clear_stack_state()
    event = sample_evolution_accepted_event(
        with_gap_snapshot=True,
        declared_self_version=5,
    )

    result = on_evolution_accepted(event)

    assert result["declaredSelfVersion"] == 5
    assert result["run_id"] == "evolve-user-aarav-v5"
    assert result["identity_stack"]["id"] == "stack-evolve-user-aarav-v5"
