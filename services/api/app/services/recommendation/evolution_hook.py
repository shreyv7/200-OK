"""Evolution accept hook — AIS M7.

Backend calls `emit_evolution_accepted` after Twin vN persist on accept.
Reject/keep paths must not call this hook — AIS performs no mutation on reject.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from sqlalchemy.orm import Session

from app.schemas import DecisionPacket, IdentityStack
from app.services.recommendation.decision_consumer import consume_gap_update
from app.services.recommendation.evolution_trigger import EvolutionAcceptedEvent
from app.services.recommendation.stack_state import apply_invalidation, get_active_stack
from app.services.recommendation.warm_cache import warm_cache_after_evolution

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


def on_evolution_accepted(
    event: EvolutionAcceptedEvent,
    *,
    db: Session | None = None,
) -> dict[str, Any]:
    """Invalidate stack assumptions and run a full re-curation against Twin vN."""
    run_id = f"evolve-{event.userId}-v{event.declaredSelfVersion}"
    packet = build_evolution_decision_packet(event)
    apply_invalidation(event.userId, packet)

    warm_result = None
    stack: IdentityStack | None = None
    if db is not None:
        warm_result = warm_cache_after_evolution(
            db,
            event.userId,
            packet,
            run_id=run_id,
        )
        if warm_result.ok:
            stack = get_active_stack(event.userId)

    return {
        "trigger": event.trigger,
        "run_id": run_id,
        "declaredSelfVersion": event.declaredSelfVersion,
        "decision_packet": packet.model_dump(),
        "identity_stack": stack.model_dump() if stack is not None else None,
        "warm_cache": {
            "ok": warm_result.ok if warm_result is not None else False,
            "reason": warm_result.reason if warm_result is not None else "no_db_session",
            "stackId": warm_result.stackId if warm_result is not None else None,
        },
    }


def emit_evolution_accepted(
    event: EvolutionAcceptedEvent,
    *,
    db: Session | None = None,
) -> dict[str, Any]:
    """In-process emitter — Backend identity service calls after Twin vN write."""
    result = on_evolution_accepted(event, db=db)
    for callback in _subscribers:
        callback(event)
    return result
