"""Prepared doomscroll intervention bundle — AIS M8."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.providers.llm.base import LLMProvider
from app.providers.search.base import SearchProvider
from app.providers.search.fake import FakeSearchProvider
from app.providers.llm.fake import FakeLLMProvider
from app.schemas import BottleneckPacket, DecisionPacket, IdentityStack, InterventionVariant
from app.services.recommendation.alternate_lens import request_alternate_stack
from app.services.recommendation.curation_cycle import run_curation_cycle
from app.services.recommendation.variants import generate_variants


@dataclass
class PreparedIntervention:
    stack: IdentityStack
    variants: list[InterventionVariant]
    alternate_stack: IdentityStack

    def variants_payload(self) -> dict[str, dict[str, Any]]:
        return {variant.intensity: variant.model_dump(mode="json") for variant in self.variants}


def prepare_doomscroll_intervention(
    user_id: str,
    *,
    decision_packet: DecisionPacket | None = None,
    run_id: str | None = None,
    llm: LLMProvider | None = None,
    search: SearchProvider | None = None,
) -> PreparedIntervention:
    """Pre-generate media stack + variants + Micro-Action alternative for beat 2."""
    packet = decision_packet or DecisionPacket(
        userId=user_id,
        gapDelta=1.5,
        invalidateStack=True,
        invalidatedElementIds=[],
        bottleneck=BottleneckPacket(
            bottleneck="execution",
            confidence=0.72,
            supporting_evidence=["fixture evidence"],
            missing_evidence=[],
            alternative_bottleneck="confidence",
        ),
        rankingFeatures={},
    )
    effective_run_id = run_id or f"prep-{user_id}"
    effective_llm = llm or FakeLLMProvider()
    effective_search = search or FakeSearchProvider()

    stack = run_curation_cycle(
        packet,
        trigger="stack.refresh",
        run_id=effective_run_id,
        llm=effective_llm,
        search=effective_search,
        persist_active_stack=True,
    )
    if not isinstance(stack, IdentityStack):
        stack = stack.stack

    variants = generate_variants(stack)
    alternate_stack = request_alternate_stack(
        user_id=user_id,
        prior_stack=stack,
        failed_lens="media",
        hypothesis_id=stack.hypothesisId,
    )
    return PreparedIntervention(stack=stack, variants=variants, alternate_stack=alternate_stack)
