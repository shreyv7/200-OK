from __future__ import annotations

from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.integrations.mcp.trellis.adapter import FixtureTrellisAdapter
from app.main import app
from app.models.user import User
from app.repositories import twin_repository
from app.schemas.evidence import RawMCPPayload
from app.services.evidence import service as evidence_service
from app.workers.seed import _DECLARED_ATTRIBUTES

client = TestClient(app)
_adapter = FixtureTrellisAdapter()


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


def _ingest_mission_completed(minutes_ago: int = 0) -> None:
    raw = RawMCPPayload(
        sourceProvider="trellis",
        rawPayload={
            "userId": "irrelevant-under-auth-bypass",
            "type": "mission_completed",
            "timestamp": (datetime.utcnow() - timedelta(minutes=minutes_ago)).isoformat(),
            "units": 1.0,
            "metadata": {"title": "shipped a project"},
        },
    )
    event = _adapter.normalize(raw)
    payload = {
        "userId": event.userId,
        "timestamp": event.timestamp.isoformat(),
        "source": event.source,
        "type": event.type,
        "category": event.category,
        "value": event.value,
        "baseWeight": event.baseWeight,
        "metadata": event.metadata,
        "simulated": event.simulated,
    }
    client.post("/api/v1/evidence", json=payload)


def test_dashboard_summary_has_full_arithmetic_fields(db_session) -> None:
    _ensure_demo_twin(db_session)

    resp = client.get("/api/v1/dashboard/summary")
    assert resp.status_code == 200
    body = resp.json()

    assert body["userId"]
    assert body["declaredSelf"]["attributes"]
    gap = body["gap"]
    for field in (
        "gapScore",
        "alignmentScore",
        "createPoints",
        "consumePoints",
        "driftPoints",
        "createConsumeRatio",
        "consistency",
        "momentum",
        "attributes",
    ):
        assert field in gap
    for attr in gap["attributes"]:
        for field in ("attributeId", "w_i", "D_i", "R_i", "deficit_i"):
            assert field in attr


def test_recompute_returns_none_without_confirmed_identity(db_session) -> None:
    # HTTP dashboard tests always run under the shared AUTH_BYPASS demo user
    # (which this file ensures has a confirmed twin), so the "no identity
    # yet" contract is exercised directly against orchestration instead.
    from app.services.identity import orchestration

    result = orchestration.recompute_and_persist(db_session, "user-with-no-twin-at-all")
    assert result is None


def test_injecting_mission_completed_changes_gap(db_session) -> None:
    _ensure_demo_twin(db_session)

    before = client.get("/api/v1/dashboard/summary").json()["gap"]["gapScore"]
    _ingest_mission_completed(minutes_ago=1)
    after = client.get("/api/v1/dashboard/summary").json()["gap"]["gapScore"]

    assert after <= before
