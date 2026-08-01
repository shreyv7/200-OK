from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_partner_matches_are_ranked() -> None:
    resp = client.get("/api/v1/partners/matches")
    assert resp.status_code == 200
    profiles = resp.json()
    assert len(profiles) == 5
    assert all("matchReason" in p for p in profiles)
    assert all(p.get("sourceBadge") for p in profiles)
    assert {p["sourceBadge"] for p in profiles} <= {
        "Simulated prototype",
        "Qdrant Cloud Match",
    }
