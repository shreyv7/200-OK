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
class CatalogFeatures:
    stage: str  # "early" | "developing" | "advancing" | "peak"
    bottleneck_label: str
    bottleneck_confidence: float
    top_deficit_attr_id: str


@dataclass
class LeverageFeatures:
    has_upcoming_event: bool
    event_id: str
    event_title: str
    days_until_event: float
    relevant_attribute_id: str
    suggested_prep_type: str  # "rehearsal" | "quick_review" | "mindset"


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
    low_confidence_flag: bool = False
    should_recurate: bool = False
    curation_intensity: str = "full"  # "full" | "light" | "micro"
    catalog_features: Optional[CatalogFeatures] = None
    leverage_features: Optional[LeverageFeatures] = None


def build_decision_packet(
    user_id: str,
    gap_result: GapResult,
    prior_gap_score: Optional[int],
    create_consume_ratio: float,
    timestamp: str,
    bottleneck_candidates: Optional[List[BottleneckCandidate]] = None,
    low_confidence_flag: bool = False,
    should_recurate: Optional[bool] = None,
    curation_intensity: str = "full",
    catalog_features: Optional[CatalogFeatures] = None,
    leverage_features: Optional[LeverageFeatures] = None,
) -> DecisionPacket:
    """Builds a DecisionPacket given GapResult and optional prior Gap score."""
    gap_delta = (gap_result.gap_score - prior_gap_score) if prior_gap_score is not None else 0
    invalidate = abs(gap_delta) >= GAP_DELTA_INVALIDATION_THRESHOLD

    if should_recurate is None:
        should_recurate = invalidate

    return DecisionPacket(
        user_id=user_id,
        gap_score=gap_result.gap_score,
        gap_delta=gap_delta,
        alignment=gap_result.alignment,
        create_consume_ratio=create_consume_ratio,
        bottleneck_candidates=bottleneck_candidates or [],
        invalidate_stack=invalidate,
        timestamp=timestamp,
        low_confidence_flag=low_confidence_flag,
        should_recurate=should_recurate,
        curation_intensity=curation_intensity,
        catalog_features=catalog_features,
        leverage_features=leverage_features,
    )
