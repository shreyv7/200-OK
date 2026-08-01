from __future__ import annotations

from datetime import datetime

from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app
from app.models.user import User
from app.repositories import twin_repository
from app.workers.seed import _DECLARED_ATTRIBUTES

client = TestClient(app)


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


def test_get_identity_returns_confirmed_declared_self(db_session) -> None:
    _ensure_demo_twin(db_session)

    resp = client.get("/api/v1/identity")
    assert resp.status_code == 200
    body = resp.json()
    assert body["version"] == 1
    ids = {a["id"] for a in body["attributes"]}
    assert "public_speaker" in ids
    assert "builder" in ids
