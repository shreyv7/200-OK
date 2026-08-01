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


def test_refresh_then_active_produces_stack_with_action_and_resource(db_session) -> None:
    _ensure_demo_twin(db_session)

    refresh_resp = client.post("/api/v1/stack/refresh")
    assert refresh_resp.status_code == 202
    assert refresh_resp.json()["status"] == "refreshing"

    active_resp = client.get("/api/v1/stack/active")
    assert active_resp.status_code == 200
    stack = active_resp.json()

    assert len(stack["elements"]) >= 2
    types = {e["type"] for e in stack["elements"]}
    assert "micro_mission" in types or "media" in types
    for element in stack["elements"]:
        assert element["explanation"]["whyThis"]
        assert element["explanation"]["whyNow"]
        assert element["explanation"]["howReducesGap"]
        assert element["sourceBadge"] in ("Live web", "Cached web", "Curated fallback")
