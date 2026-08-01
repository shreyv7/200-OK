from __future__ import annotations

from app.services.identity.scoring.constants import GAP_DELTA_INVALIDATION_THRESHOLD
from app.services.recommendation.decision_consumer import consume_gap_update
from app.services.recommendation.stack_state import clear_stack_state, get_active_stack_flags
from tests.fixtures.sample_data import sample_gap_snapshot, sample_identity_stack


def test_consume_gap_update_sets_invalidate_above_threshold() -> None:
    clear_stack_state()
    snapshot = sample_gap_snapshot(gap_delta=GAP_DELTA_INVALIDATION_THRESHOLD)

    result = consume_gap_update(snapshot)

    assert result.packet.invalidateStack is True
    assert result.flags.invalidate is True


def test_consume_gap_update_no_invalidate_below_threshold() -> None:
    clear_stack_state()
    snapshot = sample_gap_snapshot(gap_delta=GAP_DELTA_INVALIDATION_THRESHOLD - 1)

    result = consume_gap_update(snapshot)

    assert result.packet.invalidateStack is False
    assert result.flags.invalidate is False


def test_consume_gap_update_empty_stack_does_not_raise() -> None:
    clear_stack_state()
    snapshot = sample_gap_snapshot(gap_delta=10.0)

    result = consume_gap_update(snapshot, active_stack=None)

    assert result.packet.invalidatedElementIds == []
    assert result.flags.hasActiveStack is False


def test_consume_gap_update_invalidates_active_stack_elements() -> None:
    clear_stack_state()
    stack = sample_identity_stack()
    snapshot = sample_gap_snapshot(gap_delta=10.0)

    result = consume_gap_update(snapshot, active_stack=stack)

    assert result.packet.invalidateStack is True
    assert result.packet.invalidatedElementIds == ["elem-1"]
    assert get_active_stack_flags(snapshot.userId).invalidatedElementIds == ["elem-1"]
