from __future__ import annotations

from datetime import datetime

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


def test_plan_view_returns_sorted_events(db_session) -> None:
    _ensure_demo_user(db_session)
    from app.repositories import calendar_repository

    settings = get_settings()
    calendar_repository.create(db_session, settings.demo_user_id, "Later", datetime(2030, 1, 2))
    calendar_repository.create(db_session, settings.demo_user_id, "Earlier", datetime(2030, 1, 1))

    resp = client.get("/api/v1/calendar/plan-view")
    assert resp.status_code == 200
    titles = [e["title"] for e in resp.json()]
    assert titles.index("Earlier") < titles.index("Later")
