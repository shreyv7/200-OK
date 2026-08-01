from __future__ import annotations

from langgraph.checkpoint.memory import MemorySaver

from app.agents.graphs.coordinator import GRAPH_NODE_ORDER, build_coordinator_graph
from tests.fixtures.sample_data import sample_coordinator_state


def test_coordinator_graph_invokes_all_nodes() -> None:
    graph = build_coordinator_graph()
    result = graph.invoke(sample_coordinator_state())

    assert set(result["visited"]) == set(GRAPH_NODE_ORDER)
    assert result["run_id"] == "run-fixture-001"
    assert result["decision_packet"]["invalidateStack"] is True
    assert result["stack_draft"]["invalidate"] is True


def test_coordinator_graph_accepts_configurable_checkpointer() -> None:
    checkpointer = MemorySaver()
    graph = build_coordinator_graph(checkpointer=checkpointer)
    config = {"configurable": {"thread_id": "m0-test-thread"}}

    result = graph.invoke(sample_coordinator_state(), config=config)

    assert result["visited"][0] == "coordinator"
