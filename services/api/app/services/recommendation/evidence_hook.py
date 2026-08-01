"""evidence.created subscriber seam — AIS M1.

Backend M1 wires `emit_evidence_created` after persistence. Until then, tests
use the labeled STUB emitter below.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from app.agents.graphs.coordinator import build_coordinator_graph
from app.agents.graphs.run_context import CoordinatorRunContext
from app.schemas import DecisionPacket, EvidenceEvent

EvidenceSubscriber = Callable[[EvidenceEvent], dict[str, Any]]

_subscribers: list[EvidenceSubscriber] = []


def register_evidence_subscriber(callback: EvidenceSubscriber) -> None:
    """Register an additional in-process subscriber for evidence.created."""
    _subscribers.append(callback)


def build_placeholder_decision_packet(event: EvidenceEvent) -> DecisionPacket:
    """Placeholder DecisionPacket — AIS never derives Gap in M1."""
    return DecisionPacket(
        userId=event.userId,
        gapDelta=0.0,
        invalidateStack=False,
        invalidatedElementIds=[],
        bottleneck=None,
        rankingFeatures={},
    )


def on_evidence_created(event: EvidenceEvent) -> dict[str, Any]:
    """Run the Coordinator graph with a placeholder DecisionPacket (no-op curation)."""
    run_context = CoordinatorRunContext(
        run_id=f"run-{event.id}",
        trigger="evidence.created",
    )
    packet = build_placeholder_decision_packet(event)

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


def emit_evidence_created(event: EvidenceEvent) -> dict[str, Any]:
    """STUB emitter — replace with Backend evidence.created wiring on M1 merge."""
    result = on_evidence_created(event)
    for callback in _subscribers:
        callback(event)
    return result
