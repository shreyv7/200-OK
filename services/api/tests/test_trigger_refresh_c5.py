from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_post_stack_refresh_returns_202_accepted() -> None:
    with patch("app.api.stack.enqueue_tier2_stack_refresh") as mock_enqueue:
        response = client.post("/api/v1/stack/refresh")

        assert response.status_code == 202
        assert response.json() == {"status": "refreshing"}
        mock_enqueue.assert_called_once_with("demo-user-aarav")


def test_ledger_dismiss_enqueues_tier2_refresh() -> None:
    with patch(
        "app.api.ledger.enqueue_tier2_stack_refresh"
    ) as mock_enqueue:
        response = client.post(
            "/api/v1/ledger/record",
            json={
                "hypothesisId": "hyp-c5-1",
                "hypothesisFamily": "focus",
                "action": "dismissed",
            },
        )
        assert response.status_code == 200
        mock_enqueue.assert_called_once_with("demo-user-aarav")


def test_ledger_complete_enqueues_tier2_refresh() -> None:
    with patch(
        "app.api.ledger.enqueue_tier2_stack_refresh"
    ) as mock_enqueue:
        response = client.post(
            "/api/v1/ledger/record",
            json={
                "hypothesisId": "hyp-c5-2",
                "hypothesisFamily": "execution",
                "action": "completed",
            },
        )
        assert response.status_code == 200
        mock_enqueue.assert_called_once_with("demo-user-aarav")


def test_capacity_change_enqueues_tier2_refresh() -> None:
    with patch(
        "app.api.capacity.enqueue_tier2_stack_refresh"
    ) as mock_enqueue:
        response = client.patch("/api/v1/capacity", json={"value": 40.0})
        assert response.status_code == 200
        mock_enqueue.assert_called_once_with("demo-user-aarav")


def test_identity_confirm_emits_onboarding_confirmed() -> None:
    # Boot a draft via onboarding-shaped attributes, then confirm.
    attributes = [
        {
            "id": "attr-speak",
            "label": "Public speaking",
            "weight": 0.5,
            "targetWeeklyPoints": 7.5,
            "markers": [{"id": "m1", "label": "Give a talk"}],
        },
        {
            "id": "attr-ship",
            "label": "Shipping",
            "weight": 0.5,
            "targetWeeklyPoints": 7.5,
            "markers": [{"id": "m2", "label": "Ship weekly"}],
        },
    ]
    with patch(
        "app.api.identity.emit_onboarding_confirmed"
    ) as mock_emit:
        # Draft first
        draft = client.patch(
            "/api/v1/identity",
            json={"attributes": attributes, "confirm": False},
        )
        assert draft.status_code == 200
        mock_emit.assert_not_called()

        confirmed = client.patch(
            "/api/v1/identity",
            json={"attributes": attributes, "confirm": True},
        )
        assert confirmed.status_code == 200
        mock_emit.assert_called_once()
        event = mock_emit.call_args.args[0]
        assert event.userId == "demo-user-aarav"
        assert mock_emit.call_args.kwargs.get("db") is not None


def test_get_active_stack_without_identity_returns_404() -> None:
    """A5: never silently seed Aarav twin for a user with no confirmed identity."""
    # Use a fresh user id via dependency override so we don't hit demo twin leftovers.
    from app.core.di import get_current_user_id
    from app.core.db import SessionLocal
    from app.models.user import User

    fresh_id = "test-c5-no-identity-user"
    db = SessionLocal()
    try:
        if db.get(User, fresh_id) is None:
            db.add(User(id=fresh_id, capacity=100.0))
            db.commit()
    finally:
        db.close()

    app.dependency_overrides[get_current_user_id] = lambda: fresh_id
    try:
        response = client.get("/api/v1/stack/active")
        assert response.status_code == 404
        assert "onboarding" in response.json()["detail"].lower()
    finally:
        app.dependency_overrides.clear()
