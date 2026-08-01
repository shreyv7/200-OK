from __future__ import annotations

from unittest.mock import MagicMock

from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import app
from app.services.metrics import (
    get_metrics_summary,
    record_llm_usage,
    record_search_usage,
    reset_metrics,
)
from app.services.rate_limiter import check_rate_limit, reset_rate_limits

import pytest

client = TestClient(app)


def setup_function() -> None:
    reset_rate_limits()
    reset_metrics()


def test_rate_limiter_throttles_bursts_per_user() -> None:
    payload = {
        "timestamp": "2026-08-01T12:00:00Z",
        "source": "trellis",
        "type": "completion",
        "category": "creation",
        "value": 1.0,
        "baseWeight": 1.0,
    }

    # Companion telemetry allows 60 evidence POSTs / 60s per user.
    for _ in range(60):
        res = client.post("/api/v1/evidence", json=payload)
        assert res.status_code in {200, 201}

    # 61st request gets HTTP 429
    res = client.post("/api/v1/evidence", json=payload)
    assert res.status_code == 429
    assert "Rate limit exceeded" in res.json()["detail"]


def test_rate_limiter_isolates_users_directly() -> None:
    for _ in range(10):
        check_rate_limit("evidence", "isolated-user-a", limit=10, window_seconds=10)

    with pytest.raises(HTTPException) as exc_info:
        check_rate_limit("evidence", "isolated-user-a", limit=10, window_seconds=10)
    assert exc_info.value.status_code == 429

    # Different user should not be throttled
    check_rate_limit("evidence", "isolated-user-b", limit=10, window_seconds=10)


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
