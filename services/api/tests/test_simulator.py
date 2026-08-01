from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app

client = TestClient(app)


def test_simulator_gated_to_local_env() -> None:
    assert get_settings().env == "local"
    resp = client.post(
        "/api/v1/simulator/inject", json={"scenario": "doomscroll_burst", "params": {}}
    )
    assert resp.status_code != 404


def test_doomscroll_burst_injects_real_pipeline_rows() -> None:
    resp = client.post(
        "/api/v1/simulator/inject",
        json={"scenario": "doomscroll_burst", "params": {"minutes": 30}},
    )
    assert resp.status_code == 200
    events = resp.json()
    assert len(events) >= 1

    for event in events:
        assert event["source"] == "trellis"
        assert event["type"] == "focus_drift_10min"
        assert event["category"] == "focus_drift"
        assert event["simulated"] is True
        # No pre-scored Gap/score field anywhere on the injected row —
        # only the fixed fixture-adapter weight is present.
        assert event["baseWeight"] == -2.0
        assert "gapScore" not in event
        assert "score" not in event


def test_time_advance_injects_one_event() -> None:
    resp = client.post(
        "/api/v1/simulator/inject",
        json={"scenario": "time_advance", "params": {"days": 2}},
    )
    assert resp.status_code == 200
    events = resp.json()
    assert len(events) == 1
    assert events[0]["type"] == "passive_item"
