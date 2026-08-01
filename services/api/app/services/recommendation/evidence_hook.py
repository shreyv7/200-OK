"""evidence.created subscriber seam — AIS M2.

Backend wires `emit_evidence_created` after persistence and passes an optional
GapSnapshot from post-recompute KPIs. AIS never derives Gap from raw events.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from app.agents.graphs.coordinator import build_coordinator_graph
from app.agents.graphs.run_context import CoordinatorRunContext
from app.schemas import DecisionPacket, EvidenceEvent
from app.services.recommendation.decision_consumer import consume_gap_update
from app.services.recommendation.gap_snapshot import GapSnapshot
from app.services.recommendation.stack_state import get_active_stack

EvidenceSubscriber = Callable[[EvidenceEvent], dict[str, Any]]

_subscribers: list[EvidenceSubscriber] = []


def register_evidence_subscriber(callback: EvidenceSubscriber) -> None:
    """Register an additional in-process subscriber for evidence.created."""
    _subscribers.append(callback)


def build_degraded_placeholder_packet(event: EvidenceEvent) -> DecisionPacket:
    """Labeled degraded path when no GapSnapshot is available (tests / pre-M2 wiring)."""
    return DecisionPacket(
        userId=event.userId,
        gapDelta=0.0,
        invalidateStack=False,
        invalidatedElementIds=[],
        bottleneck=None,
        rankingFeatures={},
    )


# Backwards-compatible alias for M1 tests migrating to M2.
build_placeholder_decision_packet = build_degraded_placeholder_packet


def on_evidence_created(
    event: EvidenceEvent,
    *,
    gap_snapshot: GapSnapshot | None = None,
) -> dict[str, Any]:
    """Run Coordinator with a DecisionPacket from GapSnapshot or degraded placeholder."""
    run_context = CoordinatorRunContext(
        run_id=f"run-{event.id}",
        trigger="evidence.created",
    )

    if gap_snapshot is not None:
        consume_result = consume_gap_update(
            gap_snapshot,
            active_stack=get_active_stack(event.userId),
        )
        packet = consume_result.packet
    else:
        packet = build_degraded_placeholder_packet(event)

    state: dict[str, Any] = {
        "trigger": run_context.trigger,
        "run_id": run_context.run_id,
        "user_id": event.userId,
        "decision_packet": packet.model_dump(),
        "stack_draft": None,
        "visited": [],
        "evidence_id": event.id,
        "hypothesis_id": f"hyp-{run_context.run_id}",
    }

    graph = build_coordinator_graph()
    return graph.invoke(state)


def emit_evidence_created(
    event: EvidenceEvent,
    *,
    gap_snapshot: GapSnapshot | None = None,
) -> dict[str, Any]:
    """In-process emitter — Backend calls after evidence persistence + KPI recompute."""
    result = on_evidence_created(event, gap_snapshot=gap_snapshot)
    for callback in _subscribers:
        callback(event)
    return result
