#!/usr/bin/env python3
"""Live smoke for Tampermonkey Companion → Evidence Pipeline."""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8003"


def req(method: str, path: str, body: dict | None = None, headers: dict | None = None):
    data = None if body is None else json.dumps(body).encode()
    h = {"Content-Type": "application/json"}
    if headers:
        h.update(headers)
    request = urllib.request.Request(f"{BASE}{path}", data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(request, timeout=15) as resp:
            raw = resp.read().decode()
            return resp.status, json.loads(raw) if raw else None, dict(resp.headers)
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode()
        try:
            parsed = json.loads(raw) if raw else None
        except json.JSONDecodeError:
            parsed = raw
        return exc.code, parsed, dict(exc.headers)


def main() -> int:
    print(f"BASE={BASE}")
    status, health, _ = req("GET", "/api/v1/healthz")
    print("healthz", status, health)
    assert status == 200

    with urllib.request.urlopen(f"{BASE}/tampermonkey/trellis-telemetry.user.js", timeout=15) as resp:
        script = resp.read().decode()
        content_type = resp.headers.get("Content-Type")
        status = resp.status
    print("userscript", status, content_type)
    assert status == 200
    assert script.startswith("// ==UserScript==")
    assert "// ==/UserScript==" in script
    assert "@grant        GM_xmlhttpRequest" in script
    assert "instagram.com" in script and "youtube.com" in script
    print("userscript meta OK")

    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    payload = {
        "timestamp": now,
        "source": "trellis",
        "type": "session_started",
        "category": "passive_learning",
        "identityAttributeIds": [],
        "value": 1.0,
        "baseWeight": 0.5,
        "metadata": {
            "platform": "instagram",
            "originalSource": "instagram",
            "path": "/",
            "probe": "live-smoke",
        },
        "simulated": False,
    }
    status, body, _ = req("POST", "/api/v1/evidence", payload)
    print("ingest", status, body.get("id") if isinstance(body, dict) else body)
    assert status == 201, body

    status, body2, _ = req("POST", "/api/v1/evidence", payload)
    print("duplicate", status, body2.get("id") if isinstance(body2, dict) else body2)
    assert status == 200
    assert body2["id"] == body["id"]

    drift = {
        **payload,
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "type": "focus_drift_excessive_continuous_scrolling",
        "category": "focus_drift",
        "value": 6,
        "baseWeight": 0.8,
        "metadata": {
            "platform": "youtube",
            "driftType": "excessive_continuous_scrolling",
            "continuousScrolls": 6,
        },
    }
    status, drift_body, _ = req("POST", "/api/v1/evidence", drift)
    print("drift", status, drift_body.get("id") if isinstance(drift_body, dict) else drift_body)
    assert status == 201

    status, events, _ = req("GET", "/api/v1/evidence?limit=10")
    print("list", status, len(events) if isinstance(events, list) else events)
    assert status == 200
    assert any(e["id"] == body["id"] for e in events)

    status, bad, _ = req(
        "POST",
        "/api/v1/evidence",
        {
            "timestamp": "bad",
            "source": "trellis",
            "type": "x",
            "category": "passive_learning",
            "value": 1,
            "baseWeight": 0.5,
        },
    )
    print("invalid payload", status)
    assert status == 422

    status, bad_src, _ = req(
        "POST",
        "/api/v1/evidence",
        {
            "timestamp": now,
            "source": "instagram",
            "type": "session_started",
            "category": "passive_learning",
            "value": 1,
            "baseWeight": 0.5,
        },
    )
    print("invalid source", status)
    assert status == 422

    # CORS: fetch from Instagram would be blocked; GM_xmlhttpRequest bypasses CORS.
    preflight = urllib.request.Request(
        f"{BASE}/api/v1/evidence",
        method="OPTIONS",
        headers={
            "Origin": "https://www.instagram.com",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type,authorization",
        },
    )
    try:
        with urllib.request.urlopen(preflight, timeout=10) as resp:
            allow_origin = resp.headers.get("access-control-allow-origin")
            print("cors preflight", resp.status, "allow-origin=", allow_origin)
            # Instagram origin is intentionally not in CORS allow-list; Companion uses GM_xmlhttpRequest.
    except urllib.error.HTTPError as exc:
        print("cors preflight", exc.code, "(expected if origin not allow-listed)")

    # Backend unavailable
    try:
        urllib.request.urlopen("http://127.0.0.1:59999/api/v1/evidence", timeout=1)
        print("backend unavailable: unexpected success")
    except Exception as exc:
        print("backend unavailable:", type(exc).__name__, "(expected)")

    # Dashboard may 404 if onboarding incomplete — still report.
    status, dash, _ = req("GET", "/api/v1/dashboard/summary")
    print("dashboard", status, list(dash.keys()) if isinstance(dash, dict) else dash)

    print("SMOKE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
