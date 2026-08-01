"""Weekly Report / Identity Evolution run hook — AIS M7.

Routes report and evolution proposal runs through the Coordinator report branch.
"""

from __future__ import annotations

from typing import Any, Literal

from app.agents.graphs.coordinator import build_coordinator_graph
from app.schemas import DecisionPacket

ReportEvolutionTrigger = Literal["report.requested", "evolution.requested"]


def _build_report_state(
    *,
    user_id: str,
    run_id: str,
    trigger: ReportEvolutionTrigger,
    decision_packet: DecisionPacket | None = None,
) -> dict[str, Any]:
    packet = decision_packet or DecisionPacket(
        userId=user_id,
        gapDelta=0.0,
        invalidateStack=False,
        invalidatedElementIds=[],
        bottleneck=None,
        rankingFeatures={},
    )
    return {
        "trigger": trigger,
        "run_id": run_id,
        "user_id": user_id,
        "decision_packet": packet.model_dump(),
        "stack_draft": None,
        "visited": [],
        "evidence_id": None,
        "hypothesis_id": f"hyp-{run_id}",
    }


def run_report_evolution_branch(
    *,
    user_id: str,
    run_id: str,
    trigger: ReportEvolutionTrigger,
    decision_packet: DecisionPacket | None = None,
) -> dict[str, Any]:
    """Invoke the Coordinator report/evolution branch (no full curation path)."""
    state = _build_report_state(
        user_id=user_id,
        run_id=run_id,
        trigger=trigger,
        decision_packet=decision_packet,
    )
    graph = build_coordinator_graph()
    return graph.invoke(state)


def on_report_requested(
    user_id: str,
    *,
    run_id: str | None = None,
    decision_packet: DecisionPacket | None = None,
) -> dict[str, Any]:
    effective_run_id = run_id or f"report-{user_id}"
    return run_report_evolution_branch(
        user_id=user_id,
        run_id=effective_run_id,
        trigger="report.requested",
        decision_packet=decision_packet,
    )


def on_evolution_requested(
    user_id: str,
    *,
    run_id: str | None = None,
    decision_packet: DecisionPacket | None = None,
) -> dict[str, Any]:
    effective_run_id = run_id or f"evolution-{user_id}"
    return run_report_evolution_branch(
        user_id=user_id,
        run_id=effective_run_id,
        trigger="evolution.requested",
        decision_packet=decision_packet,
    )
