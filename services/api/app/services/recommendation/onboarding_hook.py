"""Onboarding confirm hook — AIS M3.

Backend calls `emit_onboarding_confirmed` after Twin v1 persist. AIS never
listens to draft interview turns or unconfirmed extractions.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from sqlalchemy.orm import Session

from app.agents.graphs.coordinator import build_coordinator_graph
from app.agents.graphs.run_context import CoordinatorRunContext
from app.schemas import DecisionPacket
from app.services.recommendation.decision_consumer import consume_gap_update
from app.services.recommendation.onboarding_trigger import OnboardingConfirmEvent
from app.services.recommendation.stack_state import get_active_stack
from app.services.recommendation.warm_cache import WarmCacheResult, warm_cache_after_onboarding

OnboardingConfirmHandler = Callable[[OnboardingConfirmEvent], dict[str, Any]]

_subscribers: list[OnboardingConfirmHandler] = []


def register_onboarding_confirm_handler(callback: OnboardingConfirmHandler) -> None:
    """Register an additional in-process handler for onboarding.confirmed."""
    _subscribers.append(callback)


def build_onboarding_decision_packet(event: OnboardingConfirmEvent) -> DecisionPacket:
    """First DecisionPacket after confirm — always invalidates stale stack assumptions."""
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


def on_onboarding_confirmed(
    event: OnboardingConfirmEvent,
    *,
    db: Session | None = None,
) -> dict[str, Any]:
    """Schedule first Coordinator DecisionPacket; warm-cache is best-effort."""
    run_context = CoordinatorRunContext(
        run_id=f"onboard-{event.userId}-v{event.twinVersion}",
        trigger="onboarding.confirmed",
    )
    packet = build_onboarding_decision_packet(event)

    state: dict[str, Any] = {
        "trigger": run_context.trigger,
        "run_id": run_context.run_id,
        "user_id": event.userId,
        "decision_packet": packet.model_dump(),
        "stack_draft": None,
        "visited": [],
        "evidence_id": None,
        "hypothesis_id": f"hyp-onboard-{event.userId}-v{event.twinVersion}",
    }

    graph = build_coordinator_graph()
    result = graph.invoke(state)

    warm_result: WarmCacheResult
    if db is not None:
        warm_result = warm_cache_after_onboarding(
            db,
            event.userId,
            packet,
            run_id=run_context.run_id,
        )
    else:
        warm_result = WarmCacheResult(ok=False, reason="no_db_session")

    result["warm_cache"] = {
        "ok": warm_result.ok,
        "reason": warm_result.reason,
        "stackId": warm_result.stackId,
    }
    return result


def emit_onboarding_confirmed(
    event: OnboardingConfirmEvent,
    *,
    db: Session | None = None,
) -> dict[str, Any]:
    """In-process emitter — Backend identity service calls after Twin v1 write."""
    result = on_onboarding_confirmed(event, db=db)
    for callback in _subscribers:
        callback(event)
    return result
