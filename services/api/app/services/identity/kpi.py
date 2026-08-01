"""KPI Snapshot Builder module for AIA.

Assembles complete growth KPI snapshot (Gap, Alignment, Create:Consume ratio, Consistency, Momentum).
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional

from app.schemas.evidence import EvidenceEvent
from app.services.identity.sanitizer import get_event_delta_days
from app.services.identity.scoring.gap import (
    EvidenceInput,
    GapResult,
    compute_create_consume,
    compute_consistency,
    compute_momentum,
)


@dataclass
class KPISnapshot:
    gapScore: int
    alignment: int
    createConsumeRatio: float
    createPoints: float
    consumePoints: float
    driftPoints: float
    consistencyScore: float
    momentumDelta: int


def build_kpi_snapshot(
    gap_result: GapResult,
    events: List[EvidenceEvent],
    prior_gap_score: Optional[int] = None,
    window_days: int = 21,
    ref_time: Optional[datetime] = None,
) -> KPISnapshot:
    """Assembles KPISnapshot combining GapResult, Create:Consume ratio, Consistency, and Momentum."""
    if ref_time is None:
        ref_time = datetime.now(timezone.utc)

    evidence_inputs: List[EvidenceInput] = []
    for e in events:
        delta = get_event_delta_days(e.timestamp, ref_time)
        if delta <= window_days:
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

    cc_result = compute_create_consume(evidence_inputs)
    consistency = compute_consistency(evidence_inputs, window_days=min(window_days, 7))
    momentum = compute_momentum(gap_result.gap_score, prior_gap_score) if prior_gap_score is not None else 0

    return KPISnapshot(
        gapScore=gap_result.gap_score,
        alignment=gap_result.alignment,
        createConsumeRatio=cc_result.ratio,
        createPoints=cc_result.create_points,
        consumePoints=cc_result.consume_points,
        driftPoints=cc_result.drift_points,
        consistencyScore=consistency,
        momentumDelta=momentum,
    )
