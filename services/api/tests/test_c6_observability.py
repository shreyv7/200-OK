from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.telemetry import (
    get_current_trace_id,
    set_telemetry_context,
    trace_id_var,
)
from app.main import app
from app.services.metrics import (
    get_metrics_summary,
    record_llm_usage,
    record_search_usage,
    reset_metrics,
)
from app.services.rate_limiter import check_rate_limit, reset_rate_limits

client = TestClient(app)


def setup_function() -> None:
    reset_rate_limits()
    reset_metrics()


def test_rate_limiter_throttles_bursts_per_user() -> None:
    headers_user_a = {"x-user-id": "user-a-burst"}
    headers_user_b = {"x-user-id": "user-b-normal"}

    payload = {
        "userId": "user-a-burst",
        "timestamp": "2026-08-01T12:00:00Z",
        "source": "trellis",
        "type": "completion",
        "category": "creation",
        "value": 1.0,
        "baseWeight": 1.0,
    }


    # User A sends 10 requests (at limit)
    for _ in range(10):
        res = client.post("/api/v1/evidence", json=payload, headers=headers_user_a)
        assert res.status_code in {200, 201}

    # 11th request for User A gets HTTP 429
    res = client.post("/api/v1/evidence", json=payload, headers=headers_user_a)
    assert res.status_code == 429
    assert "Rate limit exceeded" in res.json()["detail"]

    # User B is NOT throttled (rate limits are isolated per user)
    res_b = client.post("/api/v1/evidence", json=payload, headers=headers_user_b)
    assert res_b.status_code in {200, 201}


def test_telemetry_trace_headers_propagation() -> None:
    res = client.get("/api/v1/healthz", headers={"X-Trace-ID": "tr-custom-12345"})
    assert res.status_code == 200
    assert res.headers["X-Trace-ID"] == "tr-custom-12345"
    assert "X-Run-ID" in res.headers


def test_metrics_usage_and_cost_estimation() -> None:
    record_llm_usage("user-test-1", prompt_tokens=1000, completion_tokens=500)
    record_search_usage("user-test-1", calls=2)

    summary = get_metrics_summary("user-test-1")
    assert summary["user_id"] == "user-test-1"
    assert summary["prompt_tokens"] == 1000
    assert summary["completion_tokens"] == 500
    assert summary["total_tokens"] == 1500
    assert summary["search_calls"] == 2
    assert summary["estimated_cost_usd"] > 0.0

    global_summary = get_metrics_summary()
    assert global_summary["users_count"] == 1
    assert global_summary["total_tokens"] == 1500
