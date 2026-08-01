"""Evolution accept hook — AIS M7.

Backend calls `emit_evolution_accepted` after Twin vN persist on accept.
Reject/keep paths must not call this hook — AIS performs no mutation on reject.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from app.schemas import DecisionPacket, IdentityStack
from app.services.recommendation.curation_cycle import run_curation_cycle
from app.services.recommendation.decision_consumer import consume_gap_update
from app.services.recommendation.evolution_trigger import EvolutionAcceptedEvent
from app.services.recommendation.stack_state import apply_invalidation, get_active_stack

EvolutionAcceptHandler = Callable[[EvolutionAcceptedEvent], dict[str, Any]]

_subscribers: list[EvolutionAcceptHandler] = []


def register_evolution_accept_handler(callback: EvolutionAcceptHandler) -> None:
    _subscribers.append(callback)


def build_evolution_decision_packet(event: EvolutionAcceptedEvent) -> DecisionPacket:
    """Post-accept DecisionPacket — always invalidates stale stack assumptions."""
    if event.gapSnapshot is not None:
        consume_result = consume_gap_update(
            event.gapSnapshot,
            active_stack=get_active_stack(event.userId),
        )
        packet = consume_result.packet
    else:
        packet = DecisionPacket(
            userId=event.userId,
            gapDelta=0.0,
            invalidateStack=True,
            invalidatedElementIds=[],
            bottleneck=None,
            rankingFeatures={},
        )

    if not packet.invalidateStack:
        packet = packet.model_copy(update={"invalidateStack": True})
    return packet


def on_evolution_accepted(event: EvolutionAcceptedEvent) -> dict[str, Any]:
    """Invalidate stack assumptions and run a full re-curation against Twin vN."""
    run_id = f"evolve-{event.userId}-v{event.declaredSelfVersion}"
    packet = build_evolution_decision_packet(event)
    apply_invalidation(event.userId, packet)

    stack = run_curation_cycle(
        packet,
        trigger="evolution.accepted",
        run_id=run_id,
        persist_active_stack=True,
    )
    if not isinstance(stack, IdentityStack):
        stack = stack.stack

    return {
        "trigger": event.trigger,
        "run_id": run_id,
        "declaredSelfVersion": event.declaredSelfVersion,
        "decision_packet": packet.model_dump(),
        "identity_stack": stack.model_dump(),
        "warm_cache": {
            "ok": True,
            "reason": None,
            "stackId": stack.id,
        },
    }


def emit_evolution_accepted(event: EvolutionAcceptedEvent) -> dict[str, Any]:
    """In-process emitter — Backend identity service calls after Twin vN write."""
    result = on_evolution_accepted(event)
    for callback in _subscribers:
        callback(event)
    return result
