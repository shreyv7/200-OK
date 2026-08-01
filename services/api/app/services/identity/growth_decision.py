"""Growth Decision Engine M4 module for AIA.

Evaluates Gap score shifts, bottleneck confidence, and user capacity to determine
should_recurate, curation_intensity, and low_confidence_flag for AIS Coordinator.
"""

from dataclasses import dataclass
from typing import List, Optional

from app.services.decision.packet import BottleneckCandidate
from app.services.identity.scoring.constants import CAPACITY_FULL_MIN, CAPACITY_LIGHT_MIN, GAP_DELTA_INVALIDATION_THRESHOLD
from app.services.identity.scoring.gap import CreateConsumeResult, GapResult

LOW_CONFIDENCE_THRESHOLD = 0.65


@dataclass
class GrowthDecision:
    should_recurate: bool
    curation_intensity: str  # "full" | "light" | "micro"
    low_confidence_flag: bool
    reason: str


def evaluate_growth_decision(
    gap_result: GapResult,
    prior_gap_score: Optional[int] = None,
    bottleneck_candidates: Optional[List[BottleneckCandidate]] = None,
    create_consume: Optional[CreateConsumeResult] = None,
    capacity_pct: int = 100,
    prior_bottleneck_label: Optional[str] = None,
) -> GrowthDecision:
    """Evaluates whether stack re-curation is warranted and at what intensity."""
    gap_delta = (gap_result.gap_score - prior_gap_score) if prior_gap_score is not None else 0

    # Low-confidence flag check
    top_candidate = bottleneck_candidates[0] if bottleneck_candidates else None
    low_confidence = (top_candidate.confidence < LOW_CONFIDENCE_THRESHOLD) if top_candidate else False

    # Intensity mapping from capacity slider threshold (PRD §6 F6)
    if capacity_pct >= CAPACITY_FULL_MIN:
        intensity = "full"
    elif capacity_pct >= CAPACITY_LIGHT_MIN:
        intensity = "light"
    else:
        intensity = "micro"

    # Re-curation trigger rules
    reasons: List[str] = []
    should_recurate = False

    if abs(gap_delta) >= GAP_DELTA_INVALIDATION_THRESHOLD:
        should_recurate = True
        reasons.append(f"Gap score shifted by {gap_delta:+d} points")

    if top_candidate and prior_bottleneck_label and top_candidate.label != prior_bottleneck_label:
        should_recurate = True
        reasons.append(f"Bottleneck shifted from '{prior_bottleneck_label}' to '{top_candidate.label}'")

    if create_consume and create_consume.ratio < 0.5:
        should_recurate = True
        reasons.append(f"Create:Consume ratio critically low ({create_consume.ratio:.2f})")

    if prior_gap_score is None:
        should_recurate = True
        reasons.append("Initial stack curation cycle")

    reason_str = "; ".join(reasons) if reasons else "Gap score and bottleneck stable; no re-curation needed"

    return GrowthDecision(
        should_recurate=should_recurate,
        curation_intensity=intensity,
        low_confidence_flag=low_confidence,
        reason=reason_str,
    )
