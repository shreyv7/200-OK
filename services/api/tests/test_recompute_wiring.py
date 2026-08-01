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
