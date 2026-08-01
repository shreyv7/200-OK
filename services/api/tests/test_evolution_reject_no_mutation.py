from __future__ import annotations

from app.services.recommendation.stack_state import clear_stack_state, get_active_stack, get_active_stack_flags
from tests.fixtures.sample_data import sample_identity_stack


def test_reject_or_keep_without_accept_leaves_stack_unchanged() -> None:
    clear_stack_state()
    prior = sample_identity_stack()
    from app.services.recommendation.stack_state import set_active_stack

    set_active_stack("user-aarav", prior)
    flags_before = get_active_stack_flags("user-aarav")

    # Reject/keep is intentionally not wired — no AIS hook should fire.
    assert get_active_stack("user-aarav") == prior
    flags_after = get_active_stack_flags("user-aarav")
    assert flags_after.invalidate == flags_before.invalidate
    assert flags_after.invalidatedElementIds == flags_before.invalidatedElementIds
    assert flags_after.hypothesisId == flags_before.hypothesisId
