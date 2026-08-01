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


def test_first_two_dismissals_stay_pending() -> None:
    family = "test_family_pending_case"
    first = _record("hyp-1", family, "dismissed")
    second = _record("hyp-1", family, "dismissed")
    assert first["verdict"] == "pending"
    assert second["verdict"] == "pending"
    assert first["unlearningTriggered"] is False


def test_third_dismissal_in_window_trips_failure() -> None:
    family = "test_family_failure_case"
    _record("hyp-2", family, "dismissed")
    _record("hyp-2", family, "dismissed")
    third = _record("hyp-2", family, "dismissed")

    assert third["verdict"] == "failed"
    assert third["unlearningTriggered"] is True
    assert third["lensWeightAdjustment"] == {"media": -0.4}


def test_completed_action_marks_worked() -> None:
    result = _record("hyp-3", "test_family_worked_case", "completed")
    assert result["verdict"] == "worked"


def test_list_ledger_returns_recorded_entries() -> None:
    _record("hyp-list-test", "test_family_list_case", "delivered")
    resp = client.get("/api/v1/ledger")
    assert resp.status_code == 200
    ids = {e["hypothesisId"] for e in resp.json()}
    assert "hyp-list-test" in ids


def test_lens_weights_reflect_unlearning() -> None:
    family = "test_family_lens_weights"
    for _ in range(3):
        _record("hyp-lens", family, "dismissed")

    resp = client.get("/api/v1/ledger/lens-weights")
    assert resp.status_code == 200
    assert resp.json().get("media") == -0.4
