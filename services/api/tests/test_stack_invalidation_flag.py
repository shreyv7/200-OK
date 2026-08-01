from __future__ import annotations

from app.agents.graphs.coordinator import build_coordinator_graph
from tests.fixtures.sample_data import sample_coordinator_state, sample_decision_packet


def test_stack_draft_invalidate_from_decision_packet() -> None:
    graph = build_coordinator_graph()
    state = sample_coordinator_state()
    state["decision_packet"] = sample_decision_packet().model_dump()

    result = graph.invoke(state)

    assert result["stack_draft"]["invalidate"] is True


def test_stack_draft_invalidate_fixture_env(monkeypatch) -> None:
    monkeypatch.setenv("AIS_M1_FIXTURE_INVALIDATE", "true")

    graph = build_coordinator_graph()
    state = sample_coordinator_state()
    packet = sample_decision_packet().model_copy(update={"invalidateStack": False})
    state["decision_packet"] = packet.model_dump()

    result = graph.invoke(state)

    assert result["stack_draft"]["invalidate"] is True
