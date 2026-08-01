from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_get_active_stack_auto_refreshes_when_none_exists() -> None:
    headers = {"x-user-id": "test-c5-new-user"}
    response = client.get("/api/v1/stack/active", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["userId"] is not None

    assert "elements" in data
    assert len(data["elements"]) >= 2


def test_post_stack_refresh_returns_202_accepted() -> None:
    headers = {"x-user-id": "test-c5-refresh-user"}
    response = client.post("/api/v1/stack/refresh", headers=headers)

    assert response.status_code == 202
    assert response.json() == {"status": "refreshing"}
