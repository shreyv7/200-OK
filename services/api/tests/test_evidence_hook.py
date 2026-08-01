from __future__ import annotations

import os

from app.agents.contract_source import CONTRACT_SOURCE
from app.services.recommendation.evidence_hook import (
    build_placeholder_decision_packet,
    emit_evidence_created,
    on_evidence_created,
)
from tests.fixtures.sample_data import sample_evidence_event


def test_contract_source_is_app_schemas() -> None:
    assert CONTRACT_SOURCE == "app.schemas"


def test_on_evidence_created_runs_coordinator_with_placeholder_packet() -> None:
    event = sample_evidence_event()
    result = on_evidence_created(event)

    assert "coordinator" in result["visited"]
    packet = result["decision_packet"]
    assert packet["gapDelta"] == 0.0
    assert packet["invalidateStack"] is False
    assert packet["userId"] == event.userId


def test_emit_evidence_created_stub_does_not_derive_gap() -> None:
    event = sample_evidence_event()
    result = emit_evidence_created(event)

    assert result["decision_packet"]["gapDelta"] == 0.0
    placeholder = build_placeholder_decision_packet(event)
    assert placeholder.gapDelta == 0.0


def test_evidence_hook_registers_additional_subscriber() -> None:
    from app.services.recommendation import evidence_hook

    seen: list[str] = []

    def _subscriber(event) -> dict:
        seen.append(event.id)
        return {}

    evidence_hook._subscribers.append(_subscriber)
    try:
        event = sample_evidence_event()
        emit_evidence_created(event)
        assert event.id in seen
    finally:
        evidence_hook._subscribers.remove(_subscriber)
