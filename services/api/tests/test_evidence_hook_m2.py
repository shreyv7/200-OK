from __future__ import annotations

from app.services.recommendation.evidence_hook import on_evidence_created
from app.services.recommendation.stack_state import clear_stack_state
from tests.fixtures.sample_data import sample_evidence_event, sample_gap_snapshot


def test_on_evidence_created_with_gap_snapshot_populates_delta() -> None:
    clear_stack_state()
    event = sample_evidence_event()
    snapshot = sample_gap_snapshot(gap_delta=6.0)

    result = on_evidence_created(event, gap_snapshot=snapshot)

    packet = result["decision_packet"]
    assert packet["gapDelta"] == 6.0
    assert packet["invalidateStack"] is True
    assert result["stack_draft"]["invalidate"] is True


def test_on_evidence_created_without_snapshot_uses_degraded_placeholder() -> None:
    clear_stack_state()
    event = sample_evidence_event()

    result = on_evidence_created(event)

    assert result["decision_packet"]["gapDelta"] == 0.0
    assert result["decision_packet"]["invalidateStack"] is False
