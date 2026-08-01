from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app
from app.models.user import User

client = TestClient(app)


def _ensure_demo_user(db_session) -> None:
    settings = get_settings()
    if db_session.get(User, settings.demo_user_id) is None:
        db_session.add(User(id=settings.demo_user_id, capacity=100.0))
        db_session.commit()


def test_set_capacity_updates_user_without_moving_gap(db_session) -> None:
    _ensure_demo_user(db_session)

    resp = client.patch("/api/v1/capacity", json={"value": 20.0})
    assert resp.status_code == 200
    assert resp.json()["capacity"] == 20.0

    settings = get_settings()
    user = db_session.get(User, settings.demo_user_id)
    db_session.refresh(user)
    assert user.capacity == 20.0


def test_set_capacity_rejects_out_of_range() -> None:
    resp = client.patch("/api/v1/capacity", json={"value": 150.0})
    assert resp.status_code == 422
