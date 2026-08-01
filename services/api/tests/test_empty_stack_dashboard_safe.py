from __future__ import annotations

from app.services.recommendation.stack_assembler import assemble_stack
from app.services.recommendation.stack_state import (
    clear_stack_state,
    get_active_stack_or_safe,
    set_active_stack,
)
from tests.fixtures.sample_data import sample_decision_packet, sample_identity_stack


def test_get_active_stack_or_safe_with_no_stack() -> None:
    clear_stack_state()

    stack, flags = get_active_stack_or_safe("user-unknown")

    assert stack is None
    assert flags.hasActiveStack is False
    assert flags.invalidate is False


def test_dashboard_path_does_not_crash_when_assembling_with_packet() -> None:
    clear_stack_state()
    packet = sample_decision_packet()
    stack, flags = get_active_stack_or_safe(packet.userId)

    assert stack is None
    assembled = assemble_stack(packet, run_id="dashboard-safe")
    assert len(assembled.elements) >= 1
    assert flags.invalidate is False


def test_set_active_stack_then_safe_read() -> None:
    clear_stack_state()
    identity_stack = sample_identity_stack()
    set_active_stack(identity_stack.userId, identity_stack)

    stack, flags = get_active_stack_or_safe(identity_stack.userId)

    assert stack is not None
    assert flags.hasActiveStack is True
    assert stack.hypothesisId == "hyp-fixture-001"
