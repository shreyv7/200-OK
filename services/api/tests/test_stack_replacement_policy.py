from __future__ import annotations

from app.services.recommendation.curation_cycle import run_curation_cycle
from app.services.recommendation.stack_state import clear_stack_state
from tests.fixtures.sample_data import (
    sample_decision_packet,
    sample_prior_stack_for_replacement,
)


def test_stack_replacement_keeps_valid_mission_replaces_invalidated_media() -> None:
    clear_stack_state()
    prior = sample_prior_stack_for_replacement()
    packet = sample_decision_packet().model_copy(
        update={
            "invalidateStack": False,
            "invalidatedElementIds": ["elem-replace-media"],
        }
    )

    stack = run_curation_cycle(
        packet,
        run_id="run-replace",
        prior_stack=prior,
        persist_active_stack=False,
    )

    mission = next(e for e in stack.elements if e.type == "micro_mission")
    media = next(e for e in stack.elements if e.type in {"media", "knowledge"})

    assert mission.id == "elem-keep-mission"
    assert media.id != "elem-replace-media"


def test_invalidate_stack_replaces_all_elements() -> None:
    prior = sample_prior_stack_for_replacement()
    packet = sample_decision_packet().model_copy(update={"invalidateStack": True})

    stack = run_curation_cycle(
        packet,
        run_id="run-invalidate-all",
        prior_stack=prior,
        persist_active_stack=False,
    )

    ids = {element.id for element in stack.elements}
    assert "elem-keep-mission" not in ids
    assert "elem-replace-media" not in ids
