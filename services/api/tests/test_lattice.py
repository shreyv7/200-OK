from __future__ import annotations

from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.integrations.mcp.trellis.adapter import FixtureTrellisAdapter
from app.main import app
from app.models.user import User
from app.repositories import twin_repository
from app.schemas.evidence import RawMCPPayload
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


def _ingest_builder_commit() -> None:
    raw = RawMCPPayload(
        sourceProvider="github",
        rawPayload={
            "userId": "irrelevant-under-auth-bypass",
            "timestamp": (datetime.utcnow() - timedelta(minutes=1)).isoformat(),
            "sha": "lattice-test-sha",
            "message": "ship a feature",
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
        "metadata": {**event.metadata, "title": "ship a feature commit"},
        "simulated": event.simulated,
    }
    client.post("/api/v1/evidence", json=payload)


def test_lattice_strut_returns_contributing_events(db_session) -> None:
    _ensure_demo_twin(db_session)
    _ingest_builder_commit()

    resp = client.get("/api/v1/identity/attributes/builder/evidence")
    assert resp.status_code == 200
    body = resp.json()

    assert body["attrId"] == "builder"
    assert len(body["contributingEvents"]) >= 1
    contributor = body["contributingEvents"][0]
    for field in ("eventId", "timestamp", "baseWeight", "decayFactor", "decayedContribution"):
        assert field in contributor


def test_lattice_strut_404_for_unknown_attribute(db_session) -> None:
    _ensure_demo_twin(db_session)

    resp = client.get("/api/v1/identity/attributes/does-not-exist/evidence")
    assert resp.status_code == 404
