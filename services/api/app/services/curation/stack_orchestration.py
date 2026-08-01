"""Stack refresh wiring. Owner: Backend. milestones.md M4.

Single production curation facade: AIA DecisionPacket → AIS Coordinator graph
(`run_curation_cycle`) → DB persistence + in-memory stack sync.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.providers.llm.base import LLMProvider
from app.providers.search.base import SearchProvider
from app.repositories import intervention_repository
from app.schemas.decision import DecisionPacket
from app.schemas.stack import IdentityStack, InterventionVariant
from app.services.identity import orchestration
from app.services.recommendation.curation_cycle import CurationCycleResult, run_curation_cycle
from app.services.recommendation.guardian_gate import build_guardian_context, record_guardian_delivery
from app.services.recommendation.stack_state import set_active_stack


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


def _sync_prior_stack_from_db(db: Session, user_id: str) -> IdentityStack | None:
    row = intervention_repository.get_active(db, user_id)
    if row is None:
        return None
    stack = intervention_repository.to_stack(row)
    set_active_stack(user_id, stack)
    return stack


def _variants_to_dict(variants: list[InterventionVariant]) -> dict[str, dict]:
    return {variant.intensity: variant.model_dump(mode="json") for variant in variants}


def _persist_curation_result(db: Session, user_id: str, result: CurationCycleResult) -> IdentityStack:
    variants = _variants_to_dict(result.variants)
    intervention_repository.create(db, user_id, result.stack, variants=variants)
    set_active_stack(user_id, result.stack)
    return result.stack


def run_curation_and_persist(
    db: Session,
    user_id: str,
    decision_packet: DecisionPacket,
    search_provider: SearchProvider,
    llm_provider: LLMProvider,
    *,
    trigger: str = "stack.refresh",
    run_id: str | None = None,
) -> IdentityStack:
    """Run Coordinator graph and persist stack + variants to DB."""
    prior_stack = _sync_prior_stack_from_db(db, user_id)
    guardian_context = build_guardian_context(db, user_id)
    effective_run_id = run_id or f"curation-{user_id}"

    cycle_result = run_curation_cycle(
        decision_packet,
        trigger=trigger,
        run_id=effective_run_id,
        prior_stack=prior_stack,
        search=search_provider,
        llm=llm_provider,
        with_variants=True,
        guardian_context=guardian_context,
        persist_active_stack=True,
        db=db,
    )
    if isinstance(cycle_result, CurationCycleResult):
        stack = _persist_curation_result(db, user_id, cycle_result)
        if cycle_result.delivery_allowed:
            record_guardian_delivery(db, user_id)
        return stack

    from app.services.recommendation.variants import generate_variants

    wrapped = CurationCycleResult(
        stack=cycle_result,
        variants=generate_variants(cycle_result),
    )
    return _persist_curation_result(db, user_id, wrapped)


def refresh_stack(
    db: Session,
    user_id: str,
    search_provider: SearchProvider,
    llm_provider: LLMProvider,
) -> IdentityStack | None:
    """Runs one curation cycle and persists the resulting stack as the active
    intervention. Returns None only if there's no confirmed identity yet."""
    result = orchestration.recompute_and_persist(
        db, user_id, llm_provider=llm_provider
    )
    if result is None:
        return None

    decision_packet = _to_decision_packet(user_id, result)
    return run_curation_and_persist(
        db,
        user_id,
        decision_packet,
        search_provider,
        llm_provider,
        trigger="stack.refresh",
        run_id=f"refresh-{user_id}",
    )
