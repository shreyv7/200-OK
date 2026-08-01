from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import select

from app.core.config import get_settings
from app.integrations.mcp.trellis.adapter import FixtureTrellisAdapter
from app.main import app  # noqa: F401 — importing triggers wiring.register()
from app.models.kpi_snapshot import KPISnapshotModel
from app.models.user import User
from app.repositories import twin_repository
from app.schemas.evidence import RawMCPPayload
from app.services.evidence import service as evidence_service
from app.workers.seed import _DECLARED_ATTRIBUTES


def _ensure_demo_twin(db_session) -> None:
    settings = get_settings()
    if db_session.get(User, settings.demo_user_id) is None:
        db_session.add(User(id=settings.demo_user_id, capacity=100.0))
        db_session.commit()

    if twin_repository.get_active_declared_self(db_session, settings.demo_user_id) is None:
        twin_repository.create_version(
            db_session,
            user_id=settings.demo_user_id,
            version=1,
            attributes=_DECLARED_ATTRIBUTES,
            confirmed_at=datetime.utcnow(),
        )


def test_ingest_triggers_recompute_without_explicit_dashboard_call(db_session) -> None:
    _ensure_demo_twin(db_session)
    settings = get_settings()

    count_before = db_session.scalar(
        select(KPISnapshotModel.id)
        .where(KPISnapshotModel.user_id == settings.demo_user_id)
        .limit(1)
    )

    adapter = FixtureTrellisAdapter()
    raw = RawMCPPayload(
        sourceProvider="trellis",
        rawPayload={
            "userId": settings.demo_user_id,
            "type": "mission_completed",
            "timestamp": (datetime.utcnow() - timedelta(minutes=1)).isoformat(),
            "units": 1.0,
        },
    )
    event = adapter.normalize(raw)
    ingest_request = evidence_service.request_from_event(event)
    evidence_service.ingest(db_session, ingest_request)

    stmt = (
        select(KPISnapshotModel)
        .where(KPISnapshotModel.user_id == settings.demo_user_id)
        .order_by(KPISnapshotModel.computed_at.desc())
    )
    latest = db_session.scalars(stmt).first()

    assert latest is not None
    if count_before is None:
        assert latest.gap_score is not None


def test_gap_snapshot_conversion_matches_recompute_result() -> None:
    """Locks in the M3 prerequisite fix: wiring must translate a real
    RecomputeResult into AIS's GapSnapshot, not leave emit_evidence_created
    permanently on its degraded placeholder path."""
    from app.schemas.bottleneck import BottleneckPacket
    from app.schemas.gap import AttributeContribution, GapBreakdown
    from app.services.identity.orchestration import RecomputeResult
    from app.services.identity.wiring import _to_gap_snapshot

    gap = GapBreakdown(
        userId="u1",
        gapScore=62,
        alignmentScore=38,
        createPoints=5.0,
        consumePoints=2.0,
        driftPoints=1.0,
        createConsumeRatio=1.6,
        consistency=0.7,
        momentum=-3,
        attributes=[
            AttributeContribution(attributeId="a1", w_i=0.5, D_i=15.0, R_i=6.0, deficit_i=0.6)
        ],
    )
    result = RecomputeResult(
        gap=gap,
        bottleneck=BottleneckPacket(bottleneck="execution", confidence=0.8),
        snapshot=None,  # not needed for this conversion
        gap_delta=-6.0,
        prior_gap_score=68,
        timestamp="2026-08-01T00:00:00+00:00",
        invalidate_stack=True,
        gap_result=None,
        declared_self=None,
        events=[],
    )

    snapshot = _to_gap_snapshot("u1", result)

    assert snapshot.userId == "u1"
    assert snapshot.gapScore == 62
    assert snapshot.gapDelta == -6.0
    assert snapshot.alignment == 38
    assert snapshot.priorGapScore == 68
