from __future__ import annotations

from app.agents.graphs.coordinator import build_coordinator_graph
from app.services.recommendation.ledger_intake import (
    clear_intake_store,
    get_pending_window,
    record_evidence_ids,
)
from tests.fixtures.sample_data import sample_coordinator_state


def test_record_and_retrieve_evidence_ids() -> None:
    clear_intake_store()
    record_evidence_ids("hyp-1", ["ev-a", "ev-b"])
    record_evidence_ids("hyp-1", ["ev-b", "ev-c"])

    pending = get_pending_window("hyp-1")

    assert pending == ["ev-a", "ev-b", "ev-c"]


def test_empty_pending_window() -> None:
    clear_intake_store()
    assert get_pending_window("hyp-unknown") == []


def test_reflection_node_records_evidence_from_graph_state() -> None:
    clear_intake_store()
    graph = build_coordinator_graph()
    state = sample_coordinator_state()
    state["evidence_id"] = "ev-live-001"

    graph.invoke(state)

    hypothesis_id = "hyp-fixture-001"
    assert "ev-live-001" in get_pending_window(hypothesis_id)
