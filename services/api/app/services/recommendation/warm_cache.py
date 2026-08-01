"""Best-effort warm cache after onboarding confirm — AIS M3.

In-process only for M3; failures never propagate to the onboarding caller.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from app.schemas import DecisionPacket
from app.providers.llm.base import LLMProvider
from app.providers.search.base import SearchProvider
from app.services.recommendation.stack_assembler import assemble_stack
from app.services.recommendation.stack_state import set_active_stack

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
    """Attempt fixture stack prep + optional search; never raises."""
    try:
        if search is not None:
            search.search("onboarding warm cache", limit=1)

        stack = assemble_stack(
            decision_packet,
            run_id=run_id or f"warm-{user_id}",
            llm=llm,
            search=search,
        )
        set_active_stack(user_id, stack)
        return WarmCacheResult(ok=True, stackId=stack.id)
    except Exception as exc:  # noqa: BLE001 — warm-cache must not block onboarding
        logger.warning("warm_cache_after_onboarding failed for %s: %s", user_id, exc)
        return WarmCacheResult(ok=False, reason=str(exc))
