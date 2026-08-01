"""Map AIA Growth Decision Engine outputs → Backend app.schemas.DecisionPacket."""

from __future__ import annotations

from app.schemas import BottleneckPacket, DecisionPacket
from app.schemas.bottleneck import BottleneckLabel
from app.services.decision.packet import DecisionPacket as AiaDecisionPacket
from app.services.recommendation.gap_snapshot import GapSnapshot


def _ranking_features(
    *,
    gap_score: int | None = None,
    alignment: int | None = None,
    create_consume_ratio: float | None = None,
    consistency: float | None = None,
    momentum: float | None = None,
) -> dict[str, float]:
    features: dict[str, float] = {}
    if gap_score is not None:
        features["gapScore"] = float(gap_score)
    if alignment is not None:
        features["alignment"] = float(alignment)
    if create_consume_ratio is not None:
        features["createConsumeRatio"] = float(create_consume_ratio)
    if consistency is not None:
        features["consistency"] = float(consistency)
    if momentum is not None:
        features["momentum"] = float(momentum)
    return features


def _bottleneck_from_aia(aia_packet: AiaDecisionPacket) -> BottleneckPacket | None:
    if not aia_packet.bottleneck_candidates:
        return None
    top = aia_packet.bottleneck_candidates[0]
    label: BottleneckLabel = top.label if top.label in {
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
    } else "execution"
    alt: BottleneckLabel | None = None
    if top.alternative in {
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
    }:
        alt = top.alternative  # type: ignore[assignment]
    return BottleneckPacket(
        bottleneck=label,
        confidence=top.confidence,
        supporting_evidence=top.supporting_evidence_ids,
        missing_evidence=top.missing_evidence_ids,
        alternative_bottleneck=alt,
    )


def to_schema_decision_packet(
    aia_packet: AiaDecisionPacket,
    *,
    invalidated_element_ids: list[str] | None = None,
    consistency: float | None = None,
    momentum: float | None = None,
) -> DecisionPacket:
    """Convert AIA dataclass DecisionPacket to Backend-owned Pydantic DTO."""
    return DecisionPacket(
        userId=aia_packet.user_id,
        gapDelta=float(aia_packet.gap_delta),
        invalidateStack=aia_packet.invalidate_stack,
        invalidatedElementIds=list(invalidated_element_ids or []),
        bottleneck=_bottleneck_from_aia(aia_packet),
        rankingFeatures=_ranking_features(
            gap_score=aia_packet.gap_score,
            alignment=aia_packet.alignment,
            create_consume_ratio=aia_packet.create_consume_ratio,
            consistency=consistency,
            momentum=momentum,
        ),
    )


def from_gap_snapshot(
    snapshot: GapSnapshot,
    *,
    invalidate_stack: bool,
    invalidated_element_ids: list[str] | None = None,
) -> DecisionPacket:
    """Build schema DecisionPacket directly from a Backend-provided GapSnapshot."""
    return DecisionPacket(
        userId=snapshot.userId,
        gapDelta=float(snapshot.gapDelta),
        invalidateStack=invalidate_stack,
        invalidatedElementIds=list(invalidated_element_ids or []),
        bottleneck=None,
        rankingFeatures=_ranking_features(
            gap_score=snapshot.gapScore,
            alignment=snapshot.alignment,
            create_consume_ratio=snapshot.createConsumeRatio,
            consistency=snapshot.consistency,
            momentum=snapshot.momentum,
        ),
    )
