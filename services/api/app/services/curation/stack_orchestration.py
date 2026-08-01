"""Stack refresh wiring. Owner: Backend. milestones.md M4.

Calls AIA's recompute (via app.services.identity.orchestration, M2) to
get a current DecisionPacket, retrieves real candidates through the
cache -> Tavily -> fallback chain, and calls AIS's assemble_stack()
(app.services.recommendation.stack_assembler) with real providers.
Backend does not rank or explain — that's AIS's M4 job; this module
only wires the real infrastructure in.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.providers.llm.base import LLMProvider
from app.providers.search.base import SearchProvider
from app.repositories import intervention_repository
from app.schemas.decision import DecisionPacket
from app.schemas.stack import IdentityStack
from app.services.curation.fallback_resources import get_fallback_resources
from app.services.curation.retrieval_chain import search_with_fallback
from app.services.identity import orchestration
from app.services.recommendation.stack_assembler import assemble_stack


def _to_decision_packet(user_id: str, result: orchestration.RecomputeResult) -> DecisionPacket:
    return DecisionPacket(
        userId=user_id,
        gapDelta=result.gap_delta,
        invalidateStack=result.invalidate_stack,
        invalidatedElementIds=[],
        bottleneck=result.bottleneck,
        rankingFeatures={
            "gapScore": result.gap.gapScore,
            "alignment": result.gap.alignmentScore,
            "createConsumeRatio": result.gap.createConsumeRatio,
            "consistency": result.gap.consistency,
            "momentum": result.gap.momentum,
        },
    )


def _retrieval_query(decision_packet: DecisionPacket) -> str:
    bottleneck = decision_packet.bottleneck.bottleneck if decision_packet.bottleneck else "growth"
    return f"{bottleneck} skill-building resource for beginners"


def refresh_stack(
    db: Session,
    user_id: str,
    search_provider: SearchProvider,
    llm_provider: LLMProvider,
) -> IdentityStack | None:
    """Runs one curation cycle and persists the resulting stack as the active
    intervention. Returns None only if there's no confirmed identity yet
    (mirrors orchestration.recompute_and_persist's contract)."""
    result = orchestration.recompute_and_persist(db, user_id)
    if result is None:
        return None

    decision_packet = _to_decision_packet(user_id, result)
    query = _retrieval_query(decision_packet)

    documents, _badge = search_with_fallback(
        db, query, search_provider, get_fallback_resources
    )
    candidates = [d.model_dump() for d in documents]

    stack = assemble_stack(
        decision_packet,
        candidates=candidates,
        capacity_tier="full",
        llm=llm_provider,
        search=search_provider,
    )
    intervention_repository.create(db, user_id, stack)
    return stack
