"""End-to-end checks for Trellis Companion (Tampermonkey) integration."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app
from app.models.user import User
from app.repositories import twin_repository
from app.workers.seed import _DECLARED_ATTRIBUTES

client = TestClient(app)


def _ensure_demo_twin(db_session) -> None:
    settings = get_settings()
    if db_session.get(User, settings.demo_user_id) is None:
        db_session.add(User(id=settings.demo_user_id, capacity=100.0))
        db_session.commit()
    if twin_repository.get_active_declared_self(db_session, settings.demo_user_id) is None:
        twin_repository.create_version(
            db_session,
            user_id=settings.demo_user_id,
            version=1,
            attributes=_DECLARED_ATTRIBUTES,
            confirmed_at=datetime.now(timezone.utc),
        )


def test_userscript_is_served_for_one_click_install() -> None:
    res = client.get("/tampermonkey/trellis-telemetry.user.js")
    assert res.status_code == 200
    assert "text/javascript" in res.headers.get("content-type", "")
    body = res.text
    assert body.startswith("// ==UserScript==")
    assert "// ==/UserScript==" in body
    assert "@match        https://*.instagram.com/*" in body
    assert "@match        https://*.youtube.com/*" in body
    assert "@grant        GM_xmlhttpRequest" in body
    assert "POST" in body or "GM_xmlhttpRequest" in body
    assert "/api/v1/evidence" in body


def test_userscript_path_traversal_rejected() -> None:
    res = client.get("/tampermonkey/../services/api/.env")
    assert res.status_code == 404


def test_companion_payload_creates_evidence_and_updates_gap(db_session) -> None:
    """Simulate the exact payload shape emitted by the userscript."""
    _ensure_demo_twin(db_session)
    ts = datetime.now(timezone.utc) - timedelta(seconds=3)
    # Normalized Companion payload (v1.0.1+ maps browsing → passive_item).
    payload = {
        "timestamp": ts.isoformat().replace("+00:00", "Z"),
        "source": "trellis",
        "type": "passive_item",
        "category": "passive_learning",
        "identityAttributeIds": [],
        "value": 1.0,
        "baseWeight": 0.5,
        "metadata": {
            "platform": "instagram",
            "originalSource": "instagram",
            "companionEventType": "session_started",
            "path": "/",
            "probe": "tampermonkey-e2e",
        },
        "simulated": False,
    }

    created = client.post("/api/v1/evidence", json=payload)
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["source"] == "trellis"
    assert body["category"] == "passive_learning"
    assert body["type"] == "passive_item"
    assert body["metadata"]["platform"] == "instagram"
    assert body["userId"]

    listed = client.get("/api/v1/evidence?limit=50")
    assert listed.status_code == 200
    assert any(e["id"] == body["id"] for e in listed.json())

    # Duplicate (same user/source/type/timestamp/value) is idempotent.
    again = client.post("/api/v1/evidence", json=payload)
    assert again.status_code == 200
    assert again.json()["id"] == body["id"]

    # Focus-drift style event from Companion (normalized to focus_drift_10min).
    drift_ts = datetime.now(timezone.utc)
    drift = {
        "timestamp": drift_ts.isoformat().replace("+00:00", "Z"),
        "source": "trellis",
        "type": "focus_drift_10min",
        "category": "focus_drift",
        "identityAttributeIds": [],
        "value": 8.0,
        "baseWeight": 0.8,
        "metadata": {
            "platform": "instagram",
            "companionEventType": "focus_drift_excessive_continuous_scrolling",
            "driftType": "excessive_continuous_scrolling",
            "continuousScrolls": 8,
        },
        "simulated": False,
    }
    drift_res = client.post("/api/v1/evidence", json=drift)
    assert drift_res.status_code == 201, drift_res.text

    dashboard = client.get("/api/v1/dashboard/summary")
    assert dashboard.status_code == 200
    summary = dashboard.json()
    assert summary["userId"]
    assert "gap" in summary
    assert "gapScore" in summary["gap"]
    # Companion events must affect create/consume/drift buckets.
    assert summary["gap"]["consumePoints"] > 0 or summary["gap"]["driftPoints"] != 0


def test_invalid_companion_payload_rejected() -> None:
    res = client.post(
        "/api/v1/evidence",
        json={
            "timestamp": "not-a-date",
            "source": "trellis",
            "type": "session_started",
            "category": "passive_learning",
            "value": 1.0,
            "baseWeight": 0.5,
        },
    )
    assert res.status_code == 422


def test_disallowed_source_rejected() -> None:
    # Instagram is remapped to trellis by the userscript; raw "instagram" is invalid.
    res = client.post(
        "/api/v1/evidence",
        json={
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "source": "instagram",
            "type": "session_started",
            "category": "passive_learning",
            "value": 1.0,
            "baseWeight": 0.5,
        },
    )
    assert res.status_code == 422
