from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.schemas import DecisionPacket, IdentityStack, StackElement, StackExplanation
from app.providers.llm.fake import FakeLLMProvider
from app.providers.llm.base import LLMProvider
from app.providers.search.fake import FakeSearchProvider
from app.providers.search.base import SearchProvider


def build_providers(
    llm: LLMProvider | None = None,
    search: SearchProvider | None = None,
) -> tuple[LLMProvider, SearchProvider]:
    """Factory seam for DI; Backend Depends() will inject real providers in M3+."""
    return llm or FakeLLMProvider(), search or FakeSearchProvider()


def assemble_stack(
    decision_packet: DecisionPacket,
    candidates: list[dict[str, Any]] | None = None,
    capacity_tier: str = "full",
    ledger_weights: dict[str, float] | None = None,
    *,
    run_id: str | None = None,
    llm: LLMProvider | None = None,
    search: SearchProvider | None = None,
) -> IdentityStack:
    """Assemble the smallest coherent Identity Stack for the current bottleneck.

    M1 returns a fixture-valid stack. M4+ will retrieve, rank, and explain.
    Never returns an empty stack — falls back to curated fixture elements.
    """
    _llm, _search = build_providers(llm, search)
    _ = (_llm, _search, candidates, capacity_tier, ledger_weights)

    stack_key = run_id or decision_packet.userId
    hypothesis_id = f"hyp-{stack_key}"
    now = datetime.now(timezone.utc)
    bottleneck = (
        decision_packet.bottleneck.bottleneck
        if decision_packet.bottleneck is not None
        else "execution"
    )

    elements = [
        StackElement(
            id="elem-action-1",
            type="micro_mission",
            title="Ship a 60-second speaking clip",
            sourceBadge="Curated fallback",
            explanation=StackExplanation(
                whyThis="Targets the execution bottleneck with the smallest publishable action.",
                whyNow="Gap invalidation or drift trigger requested a refreshed stack.",
                howReducesGap="Creation evidence raises Revealed Self toward the declared speaker target.",
            ),
        ),
        StackElement(
            id="elem-resource-1",
            type="media",
            title="How to structure a one-minute talk",
            url="https://example.com/one-minute-talk",
            sourceBadge="Curated fallback",
            explanation=StackExplanation(
                whyThis="Supports the micro-mission with a concrete structure.",
                whyNow=f"Paired with the action while capacity tier is {capacity_tier}.",
                howReducesGap="Passive learning plus immediate application closes the say-do gap.",
            ),
        ),
    ]

    return IdentityStack(
        id=f"stack-{stack_key}",
        userId=decision_packet.userId,
        hypothesisId=hypothesis_id,
        bottleneck=bottleneck,
        elements=elements,
        curatedAt=now,
    )
