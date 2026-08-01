from __future__ import annotations

from app.agents.graphs.coordinator import build_coordinator_graph
from tests.fixtures.sample_data import sample_coordinator_state, sample_decision_packet_with_bottleneck


def test_planner_targets_bottleneck() -> None:
    packet = sample_decision_packet_with_bottleneck(bottleneck="confidence")
    state = sample_coordinator_state()
    state["decision_packet"] = packet.model_dump()

    result = build_coordinator_graph().invoke(state)
    stack_data = result["identity_stack"]
    mission = next(e for e in stack_data["elements"] if e["type"] == "micro_mission")

    assert "share" in mission["title"].lower() or "clip" in mission["title"].lower()
    assert stack_data["bottleneck"] == "confidence"
