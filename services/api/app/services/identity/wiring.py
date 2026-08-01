"""Registers the evidence.created -> Gap recompute hook. Owner: Backend.

Closes two loops from milestones.md:
1. M2: "Recompute on every accepted evidence event (called from Backend
   service)" — recompute_and_persist.
2. AIS's M2 evidence_hook seam (merged to dev in 3f8f384): "Backend wires
   `emit_evidence_created` after persistence and passes an optional
   GapSnapshot from post-recompute KPIs." Left dangling in M2 pending
   review; closed here in M3 as a small prerequisite since AIS's real
   consumer (decision_consumer.py) now depends on it — this only adds a
   caller, it does not modify any AIS-owned file.
"""

from __future__ import annotations

from app.core.db import SessionLocal
from app.models.evidence_event import EvidenceEventModel
from app.repositories import evidence_repository
from app.services.evidence import service as evidence_service
from app.services.identity import orchestration
from app.services.recommendation.evidence_hook import emit_evidence_created
from app.services.recommendation.gap_snapshot import GapSnapshot


def _to_gap_snapshot(user_id: str, result: orchestration.RecomputeResult) -> GapSnapshot:
    return GapSnapshot(
        userId=user_id,
        gapScore=result.gap.gapScore,
        gapDelta=result.gap_delta,
        alignment=result.gap.alignmentScore,
        createConsumeRatio=result.gap.createConsumeRatio,
        consistency=result.gap.consistency,
        momentum=float(result.gap.momentum),
        timestamp=result.timestamp,
        priorGapScore=result.prior_gap_score,
    )


def _on_evidence_created(row: EvidenceEventModel) -> None:
    db = SessionLocal()
    try:
        result = orchestration.recompute_and_persist(db, row.user_id)
        event = evidence_repository.to_schema(row)
        gap_snapshot = _to_gap_snapshot(row.user_id, result) if result is not None else None
        emit_evidence_created(event, gap_snapshot=gap_snapshot)
    finally:
        db.close()


def register() -> None:
    evidence_service.on_evidence_created(_on_evidence_created)
