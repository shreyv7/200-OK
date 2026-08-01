"""DecisionPacket dataclass and Growth Decision Engine contracts.

Consumed by AIS Coordinator to drive continuous curation stack updates.
"""

from dataclasses import dataclass, field
from typing import List, Optional

from app.services.identity.scoring.constants import GAP_DELTA_INVALIDATION_THRESHOLD
from app.services.identity.scoring.gap import GapResult


BOTTLENECK_TAXONOMY: List[str] = [
    "confidence",
    "consistency",
    "execution",
    "accountability",
    "knowledge",
    "communication",
    "focus",
    "networking",
    "discipline",
    "burnout",
]


@dataclass
class BottleneckCandidate:
    label: str
    confidence: float
    supporting_evidence_ids: List[str] = field(default_factory=list)
    missing_evidence_ids: List[str] = field(default_factory=list)
    alternative: Optional[str] = None


@dataclass
class DecisionPacket:
    user_id: str
    gap_score: int
    gap_delta: int
    alignment: int
    create_consume_ratio: float
    bottleneck_candidates: List[BottleneckCandidate]
    invalidate_stack: bool
    timestamp: str


def build_decision_packet(
    user_id: str,
    gap_result: GapResult,
    prior_gap_score: Optional[int],
    create_consume_ratio: float,
    timestamp: str,
    bottleneck_candidates: Optional[List[BottleneckCandidate]] = None,
) -> DecisionPacket:
    """Builds a DecisionPacket given GapResult and optional prior Gap score."""
    gap_delta = (gap_result.gap_score - prior_gap_score) if prior_gap_score is not None else 0
    invalidate = abs(gap_delta) >= GAP_DELTA_INVALIDATION_THRESHOLD

    return DecisionPacket(
        user_id=user_id,
        gap_score=gap_result.gap_score,
        gap_delta=gap_delta,
        alignment=gap_result.alignment,
        create_consume_ratio=create_consume_ratio,
        bottleneck_candidates=bottleneck_candidates or [],
        invalidate_stack=invalidate,
        timestamp=timestamp,
    )
