from __future__ import annotations

from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _payload(event_type: str, minutes_ago: int = 0, value: float = 1.0) -> dict:
    # userId is ignored by the API (attributed to the authenticated/bypassed
    # user instead); event_type is used as a unique marker per test since all
    # HTTP requests share one demo user under AUTH_BYPASS.
    return {
        "userId": "irrelevant-under-auth-bypass",
        "timestamp": (datetime.utcnow() - timedelta(minutes=minutes_ago)).isoformat(),
        "source": "trellis",
        "type": event_type,
        "category": "creation",
        "value": value,
        "baseWeight": 3.0,
        "metadata": {},
        "simulated": True,
    }


def test_post_then_get_roundtrip() -> None:
    payload = _payload("test_type_roundtrip")

    post_resp = client.post("/api/v1/evidence", json=payload)
    assert post_resp.status_code == 201
    body = post_resp.json()
    assert body["simulated"] is True

    get_resp = client.get("/api/v1/evidence")
    assert get_resp.status_code == 200
    events = get_resp.json()
    assert any(e["id"] == body["id"] for e in events)


def test_duplicate_post_is_idempotent() -> None:
    payload = _payload("test_type_dedupe", minutes_ago=5)

    first = client.post("/api/v1/evidence", json=payload)
    assert first.status_code == 201

    second = client.post("/api/v1/evidence", json=payload)
    assert second.status_code == 200
    assert second.json()["id"] == first.json()["id"]

    get_resp = client.get("/api/v1/evidence")
    matching = [e for e in get_resp.json() if e["type"] == "test_type_dedupe"]
    assert len(matching) == 1


def test_evidence_created_listener_fires_once_per_new_event() -> None:
    from app.services.evidence import service as evidence_service

    fired: list[str] = []
    evidence_service.on_evidence_created(lambda row: fired.append(row.id))

    payload = _payload("test_type_listener", minutes_ago=10)

    client.post("/api/v1/evidence", json=payload)
    client.post("/api/v1/evidence", json=payload)  # duplicate — must not re-fire

    get_resp = client.get("/api/v1/evidence")
    row_id = next(e["id"] for e in get_resp.json() if e["type"] == "test_type_listener")
    assert fired.count(row_id) == 1
