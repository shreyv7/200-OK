"""Gap Recomputation Service Orchestrator module for AIA.

Pure entrypoint called on evidence ingest to recompute GapResult, KPISnapshot, and DecisionPacket.
Enforces Gap Firewall: bottleneck diagnosis never modifies Gap score arithmetic.
"""

from datetime import datetime, timezone
from typing import Any, List, Optional, Tuple

from app.schemas.evidence import EvidenceEvent
from app.schemas.identity import DeclaredSelf
from app.services.decision.packet import DecisionPacket, build_decision_packet
from app.services.identity.bottleneck_v0 import diagnose_bottleneck_v0
from app.services.identity.bottleneck_v1 import diagnose_bottleneck_v1
from app.services.identity.growth_decision import evaluate_growth_decision
from app.services.identity.kpi import KPISnapshot, build_kpi_snapshot
from app.services.identity.sanitizer import get_event_delta_days
from app.services.identity.scoring.gap import (
    AttrInput,
    EvidenceInput,
    GapResult,
    compute_consistency,
    compute_create_consume,
    compute_gap_score,
)


def recompute_user_gap(
    user_id: str,
    declared_self: DeclaredSelf,
    events: List[EvidenceEvent],
    prior_gap_score: Optional[int] = None,
    window_days: int = 21,
    ref_time: Optional[datetime] = None,
    llm_provider: Optional[Any] = None,
    capacity_pct: int = 100,
    prior_bottleneck_label: Optional[str] = None,
) -> Tuple[GapResult, KPISnapshot, DecisionPacket]:
    """Recomputes deterministic GapResult, KPISnapshot, and DecisionPacket for user_id."""
    if ref_time is None:
        ref_time = datetime.now(timezone.utc)

    timestamp_str = ref_time.isoformat()

    attr_inputs = [
        AttrInput(
            attr_id=attr.id,
            w_i=attr.weight,
            D_i=attr.targetWeeklyPoints,
        )
        for attr in declared_self.attributes
    ]

    evidence_inputs: List[EvidenceInput] = []
    window_events: List[EvidenceEvent] = []

    for e in events:
        delta = get_event_delta_days(e.timestamp, ref_time)
        if delta <= window_days:
            window_events.append(e)
            for attr_id in (e.identityAttributeIds or ["unmapped"]):
                evidence_inputs.append(
                    EvidenceInput(
                        event_type=e.type,
                        attr_id=attr_id,
                        a_ik=1.0,
                        delta_days=delta,
                        value_override=e.value,
                    )
                )

    # 1. Deterministic Gap score math (Gap Firewall: no LLM input)
    gap_result = compute_gap_score(attr_inputs, evidence_inputs)
    kpi_snapshot = build_kpi_snapshot(
        gap_result, window_events, prior_gap_score=prior_gap_score, window_days=window_days, ref_time=ref_time
    )

    cc_result = compute_create_consume(evidence_inputs)
    consistency = compute_consistency(evidence_inputs, window_days=min(window_days, 7))

    # 2. Bottleneck diagnosis (v1 if llm_provider available, else v0 fallback)
    if llm_provider is not None:
        bottleneck_candidates = diagnose_bottleneck_v1(
            gap_result, cc_result, consistency, window_events, llm_provider, user_id
        )
    else:
        bottleneck_candidates = diagnose_bottleneck_v0(gap_result, cc_result, consistency, window_events)

    # 3. Growth Decision Engine evaluation
    growth_decision = evaluate_growth_decision(
        gap_result=gap_result,
        prior_gap_score=prior_gap_score,
        bottleneck_candidates=bottleneck_candidates,
        create_consume=cc_result,
        capacity_pct=capacity_pct,
        prior_bottleneck_label=prior_bottleneck_label,
    )

    # 4. DecisionPacket assembly
    decision_packet = build_decision_packet(
        user_id=user_id,
        gap_result=gap_result,
        prior_gap_score=prior_gap_score,
        create_consume_ratio=cc_result.ratio,
        timestamp=timestamp_str,
        bottleneck_candidates=bottleneck_candidates,
        low_confidence_flag=growth_decision.low_confidence_flag,
        should_recurate=growth_decision.should_recurate,
        curation_intensity=growth_decision.curation_intensity,
    )

    return gap_result, kpi_snapshot, decision_packet
