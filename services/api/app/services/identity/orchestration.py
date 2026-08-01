"""Backend-owned wiring for AIA's deterministic Gap/KPI/bottleneck functions.

Distinct from `app/services/identity/*` (AIA's pure, DB-free modules):
this module is the only place that talks to the database and turns
AIA's pure dataclasses into Backend's frozen Pydantic schemas. AIA owns
the arithmetic; Backend owns calling it and persisting/serving results
(milestones.md M2, techstack.md §17 "Deterministic before LLM").
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.kpi_snapshot import KPISnapshotModel
from app.repositories import evidence_repository, twin_repository
from app.schemas.bottleneck import BottleneckPacket
from app.schemas.gap import AttributeContribution, GapBreakdown
from app.services.identity.enrichment import enrich_evidence_event
from app.services.identity.recompute import recompute_user_gap

WINDOW_DAYS = 21


@dataclass
class RecomputeResult:
    gap: GapBreakdown
    bottleneck: BottleneckPacket | None
    snapshot: KPISnapshotModel
    gap_delta: float
    prior_gap_score: int | None
    timestamp: str


def _latest_snapshot(db: Session, user_id: str) -> KPISnapshotModel | None:
    stmt = (
        select(KPISnapshotModel)
        .where(KPISnapshotModel.user_id == user_id)
        .order_by(KPISnapshotModel.computed_at.desc())
    )
    return db.scalars(stmt).first()


def _top_bottleneck_packet(candidates) -> BottleneckPacket | None:
    if not candidates:
        return None
    top = max(candidates, key=lambda c: c.confidence)
    return BottleneckPacket(
        bottleneck=top.label,
        confidence=top.confidence,
        supporting_evidence=top.supporting_evidence_ids,
        missing_evidence=top.missing_evidence_ids,
        alternative_bottleneck=top.alternative,
    )


def recompute_and_persist(db: Session, user_id: str) -> RecomputeResult | None:
    """Recompute Gap/KPI/bottleneck for user_id and persist a KPI snapshot row.

    Returns None if there is no confirmed DeclaredSelf yet — normal before
    the Mirror Interview (M3) or the seed fixture twin has run.
    """
    declared_self = twin_repository.get_active_declared_self(db, user_id)
    if declared_self is None:
        return None

    rows = evidence_repository.list_window(db, user_id, limit=1000)
    events = [evidence_repository.to_schema(row) for row in rows]
    events = [enrich_evidence_event(e, declared_self) for e in events]

    prior = _latest_snapshot(db, user_id)
    prior_gap_score = prior.gap_score if prior is not None else None

    gap_result, kpi, decision_packet = recompute_user_gap(
        user_id=user_id,
        declared_self=declared_self,
        events=events,
        prior_gap_score=prior_gap_score,
        window_days=WINDOW_DAYS,
    )

    gap_breakdown = GapBreakdown(
        userId=user_id,
        gapScore=gap_result.gap_score,
        alignmentScore=gap_result.alignment,
        createPoints=kpi.createPoints,
        consumePoints=kpi.consumePoints,
        driftPoints=kpi.driftPoints,
        createConsumeRatio=kpi.createConsumeRatio,
        consistency=kpi.consistencyScore,
        momentum=kpi.momentumDelta,
        attributes=[
            AttributeContribution(
                attributeId=attr.attr_id,
                w_i=attr.w_i,
                D_i=attr.D_i,
                R_i=attr.R_i,
                deficit_i=attr.deficit,
            )
            for attr in gap_result.per_attribute
        ],
    )
    bottleneck_packet = _top_bottleneck_packet(decision_packet.bottleneck_candidates)

    snapshot = KPISnapshotModel(
        user_id=user_id,
        gap_score=gap_result.gap_score,
        alignment=gap_result.alignment,
        create_consume_ratio=kpi.createConsumeRatio,
        create_points=kpi.createPoints,
        consume_points=kpi.consumePoints,
        drift_points=kpi.driftPoints,
        consistency=kpi.consistencyScore,
        momentum=kpi.momentumDelta,
        per_attribute=[a.model_dump() for a in gap_breakdown.attributes],
    )
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)

    return RecomputeResult(
        gap=gap_breakdown,
        bottleneck=bottleneck_packet,
        snapshot=snapshot,
        gap_delta=float(decision_packet.gap_delta),
        prior_gap_score=prior_gap_score,
        timestamp=decision_packet.timestamp,
    )
