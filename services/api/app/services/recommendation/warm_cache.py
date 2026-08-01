"""Best-effort warm cache after onboarding confirm — AIS M3/M4."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from app.schemas import DecisionPacket
from app.providers.llm.base import LLMProvider
from app.providers.search.base import SearchProvider
from app.services.recommendation.curation_cycle import run_curation_cycle

logger = logging.getLogger(__name__)


@dataclass
class WarmCacheResult:
    ok: bool
    reason: str | None = None
    stackId: str | None = None


def warm_cache_after_onboarding(
    user_id: str,
    decision_packet: DecisionPacket,
    *,
    run_id: str | None = None,
    llm: LLMProvider | None = None,
    search: SearchProvider | None = None,
) -> WarmCacheResult:
    """Attempt full curation cycle prep; never raises."""
    try:
        stack = run_curation_cycle(
            decision_packet,
            trigger="onboarding.confirmed",
            run_id=run_id or f"warm-{user_id}",
            llm=llm,
            search=search,
            persist_active_stack=True,
        )
        return WarmCacheResult(ok=True, stackId=stack.id)
    except Exception as exc:  # noqa: BLE001 — warm-cache must not block onboarding
        logger.warning("warm_cache_after_onboarding failed for %s: %s", user_id, exc)
        return WarmCacheResult(ok=False, reason=str(exc))


def warm_cache_after_evolution(
    user_id: str,
    decision_packet: DecisionPacket,
    *,
    run_id: str | None = None,
    llm: LLMProvider | None = None,
    search: SearchProvider | None = None,
) -> WarmCacheResult:
    """Best-effort refresh after evolution accept; never raises."""
    try:
        stack = run_curation_cycle(
            decision_packet,
            trigger="evolution.accepted",
            run_id=run_id or f"warm-evolve-{user_id}",
            llm=llm,
            search=search,
            persist_active_stack=True,
        )
        stack_id = stack.id if hasattr(stack, "id") else stack.stack.id
        return WarmCacheResult(ok=True, stackId=stack_id)
    except Exception as exc:  # noqa: BLE001 — warm-cache must not block accept path
        logger.warning("warm_cache_after_evolution failed for %s: %s", user_id, exc)
        return WarmCacheResult(ok=False, reason=str(exc))
