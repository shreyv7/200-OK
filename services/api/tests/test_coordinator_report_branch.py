from __future__ import annotations

from app.agents.graphs.coordinator import GRAPH_NODE_ORDER, build_coordinator_graph
from app.services.recommendation.report_evolution_hook import on_evolution_requested, on_report_requested
from tests.fixtures.sample_data import sample_coordinator_state, sample_report_requested_state


def test_report_requested_routes_to_report_slot_only() -> None:
    graph = build_coordinator_graph()
    result = graph.invoke(sample_report_requested_state())

    assert result["visited"] == ["coordinator", "report_evolution"]
    assert "knowledge" not in result["visited"]
    assert "assemble" not in result["visited"]
    assert result["report_evolution_result"]["trigger"] == "report.requested"


def test_evolution_requested_routes_to_report_slot_only() -> None:
    result = on_evolution_requested("user-aarav", run_id="run-evolution-proposal")

    assert result["visited"] == ["coordinator", "report_evolution"]
    assert "planner" not in result["visited"]
    assert result["report_evolution_result"]["trigger"] == "evolution.requested"


def test_curation_run_still_traverses_full_graph() -> None:
    graph = build_coordinator_graph()
    result = graph.invoke(sample_coordinator_state())

    assert set(result["visited"]) == set(GRAPH_NODE_ORDER)
    assert "report_evolution" not in result["visited"]
    assert result.get("identity_stack") is not None


def test_on_report_requested_returns_pending_seam_payload() -> None:
    result = on_report_requested("user-aarav", run_id="run-report-hook")

    assert result["report_evolution_result"]["status"] == "pending"
    assert result["run_id"] == "run-report-hook"
