"""Best-effort warm cache after onboarding/evolution confirm — AIS M3/M4."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.di import get_llm_provider, get_search_provider
from app.providers.llm.base import LLMProvider
from app.providers.search.base import SearchProvider
from app.schemas import DecisionPacket
from app.services.curation import stack_orchestration

logger = logging.getLogger(__name__)


@dataclass
class WarmCacheResult:
    ok: bool
    reason: str | None = None
    stackId: str | None = None


def warm_cache_after_onboarding(
    db: Session,
    user_id: str,
    decision_packet: DecisionPacket,
    *,
    run_id: str | None = None,
    llm: LLMProvider | None = None,
    search: SearchProvider | None = None,
) -> WarmCacheResult:
    """Attempt full curation via Coordinator facade; never raises."""
    settings = get_settings()
    effective_llm = llm or get_llm_provider(settings)
    effective_search = search or get_search_provider(settings)
    try:
        stack = stack_orchestration.run_curation_and_persist(
            db,
            user_id,
            decision_packet,
            effective_search,
            effective_llm,
            trigger="onboarding.confirmed",
            run_id=run_id or f"warm-{user_id}",
        )
        return WarmCacheResult(ok=True, stackId=stack.id)
    except Exception as exc:  # noqa: BLE001 — warm-cache must not block onboarding
        logger.warning("warm_cache_after_onboarding failed for %s: %s", user_id, exc)
        return WarmCacheResult(ok=False, reason=str(exc))


def warm_cache_after_evolution(
    db: Session,
    user_id: str,
    decision_packet: DecisionPacket,
    *,
    run_id: str | None = None,
    llm: LLMProvider | None = None,
    search: SearchProvider | None = None,
) -> WarmCacheResult:
    """Best-effort refresh after evolution accept; never raises."""
    settings = get_settings()
    effective_llm = llm or get_llm_provider(settings)
    effective_search = search or get_search_provider(settings)
    try:
        stack = stack_orchestration.run_curation_and_persist(
            db,
            user_id,
            decision_packet,
            effective_search,
            effective_llm,
            trigger="evolution.accepted",
            run_id=run_id or f"warm-evolve-{user_id}",
        )
        return WarmCacheResult(ok=True, stackId=stack.id)
    except Exception as exc:  # noqa: BLE001 — warm-cache must not block accept path
        logger.warning("warm_cache_after_evolution failed for %s: %s", user_id, exc)
        return WarmCacheResult(ok=False, reason=str(exc))
