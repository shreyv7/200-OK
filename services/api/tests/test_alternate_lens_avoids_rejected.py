from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.services.recommendation.alternate_lens import request_alternate_stack
from app.services.recommendation.intervention_action import on_intervention_action
from app.services.recommendation.ledger_intake import clear_intake_store, record_action
from app.services.recommendation.stack_state import clear_stack_state, set_active_stack
from tests.fixtures.sample_data import sample_active_stack_for_variants


def test_alternate_lens_avoids_media_after_failure() -> None:
    clear_stack_state()
    prior = sample_active_stack_for_variants()
    set_active_stack("user-aarav", prior)

    alternate = request_alternate_stack(
        user_id="user-aarav",
        prior_stack=prior,
        failed_lens="media",
        hypothesis_id=prior.hypothesisId,
    )

    assert all(element.type != "media" for element in alternate.elements)
    assert any(element.type == "micro_mission" for element in alternate.elements)


def test_unlearning_tags_on_third_dismissal() -> None:
    clear_intake_store()
    clear_stack_state()
    prior = sample_active_stack_for_variants()
    set_active_stack("user-aarav", prior)
    now = datetime.now(timezone.utc)

    record_action("user-aarav", "media-video", "dismissed", timestamp=now - timedelta(days=10))
    record_action("user-aarav", "media-video", "dismissed", timestamp=now - timedelta(days=5))

    outcome = on_intervention_action(
        "user-aarav",
        prior.hypothesisId,
        "media-video",
        "dismissed",
        timestamp=now,
        failed_lens="media",
    )

    assert outcome.ledger_entry.verdict == "failed"
    assert outcome.ledger_entry.unlearningTriggered is True
    assert outcome.ledger_entry.lensWeightAdjustment is not None
    assert outcome.alternate_stack is not None
    assert "System Unlearning" in (outcome.ledger_entry.note or "")
