from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _record(hypothesis_id: str, family: str, action: str) -> dict:
    resp = client.post(
        "/api/v1/ledger/record",
        json={"hypothesisId": hypothesis_id, "hypothesisFamily": family, "action": action},
    )
    assert resp.status_code == 200
    return resp.json()


def test_adaptations_excludes_non_unlearning_entries() -> None:
    _record("hyp-adapt-a", "test_family_adapt_a", "delivered")
    _record("hyp-adapt-a", "test_family_adapt_a", "completed")

    adaptations = client.get("/api/v1/ledger/adaptations").json()
    ids = {e["hypothesisId"] for e in adaptations}
    assert "hyp-adapt-a" not in ids


def test_adaptations_includes_unlearning_triggered_entries() -> None:
    family = "test_family_adapt_b"
    _record("hyp-adapt-b", family, "dismissed")
    _record("hyp-adapt-b", family, "dismissed")
    third = _record("hyp-adapt-b", family, "dismissed")
    assert third["unlearningTriggered"] is True

    adaptations = client.get("/api/v1/ledger/adaptations").json()
    ids = {e["hypothesisId"] for e in adaptations}
    assert "hyp-adapt-b" in ids
