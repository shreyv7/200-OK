from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_healthz() -> None:
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readyz_does_not_crash_without_db() -> None:
    response = client.get("/readyz")
    assert response.status_code in (200, 503)
