"""Tests for Integrations Router (OAuth Connect, Callback, Status, Revoke). Owner: Person D."""

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.core.db import get_db
from app.core.oauth_state import generate_oauth_state
from app.core.security_tokens import decrypt_token
from app.integrations.oauth_exchange import TokenResponse
from app.main import app
from app.models.base import Base
from app.models.integration_connection import IntegrationConnection
from app.repositories.integration_repository import IntegrationRepository
from app.api.integrations import ensure_fresh_token


TEST_DATABASE_URL = "sqlite:///./test_integrations_router.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db
    yield
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()


@pytest.fixture
def client():
    return TestClient(app)


def test_status_empty_returns_empty_list(client):
    response = client.get("/api/v1/integrations/status")
    assert response.status_code == 200
    assert response.json() == []


def test_connect_returns_auth_url_google(client):
    response = client.get("/api/v1/integrations/google-calendar/connect")
    assert response.status_code == 200
    data = response.json()
    assert "authUrl" in data
    assert "accounts.google.com" in data["authUrl"]
    assert "state=" in data["authUrl"]


def test_connect_returns_auth_url_github(client):
    response = client.get("/api/v1/integrations/github/connect")
    assert response.status_code == 200
    data = response.json()
    assert "authUrl" in data
    assert "github.com/login/oauth/authorize" in data["authUrl"]
    assert "state=" in data["authUrl"]


def test_connect_unknown_provider_422(client):
    response = client.get("/api/v1/integrations/bogus-provider/connect")
    assert response.status_code == 422


@patch("app.api.integrations.exchange_google_code")
def test_callback_upserts_connection_and_returns_status(mock_exchange, client):
    user_id = "demo-user-aarav"
    state = generate_oauth_state(user_id, "google-calendar")
    mock_exchange.return_value = TokenResponse(
        access_token="google_access_123",
        refresh_token="google_refresh_456",
        scopes=["https://www.googleapis.com/auth/calendar.readonly"],
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )

    response = client.get(f"/api/v1/integrations/google-calendar/callback?code=mock_code_123&state={state}")
    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "google-calendar"
    assert data["connected"] is True

    # Verify DB entry
    db = TestingSessionLocal()
    repo = IntegrationRepository(db)
    conn = repo.get_active_connection(user_id, "google-calendar")
    assert conn is not None
    assert conn.access_token == "google_access_123"
    assert conn.refresh_token == "google_refresh_456"
    db.close()


def test_callback_invalid_state_403(client):
    response = client.get("/api/v1/integrations/google-calendar/callback?code=mock_code&state=invalid_tampered_state")
    assert response.status_code == 403
    assert "Invalid or tampered" in response.json()["detail"]


def test_callback_expired_state_403(client):
    user_id = "demo-user-aarav"
    state = generate_oauth_state(user_id, "google-calendar")

    with patch("app.core.oauth_state.datetime") as mock_dt:
        # Fast forward 40 minutes (> 30 min TTL)
        future = datetime.now(timezone.utc) + timedelta(minutes=40)
        mock_dt.now.return_value = future
        response = client.get(f"/api/v1/integrations/google-calendar/callback?code=mock_code&state={state}")
        assert response.status_code == 403
        assert "expired" in response.json()["detail"]


@patch("app.api.integrations.exchange_google_code")
def test_status_after_connect(mock_exchange, client):
    user_id = "demo-user-aarav"
    state = generate_oauth_state(user_id, "google-calendar")
    mock_exchange.return_value = TokenResponse(
        access_token="acc_token",
        refresh_token="ref_token",
        scopes=["https://www.googleapis.com/auth/calendar.readonly"],
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )

    client.get(f"/api/v1/integrations/google-calendar/callback?code=code_1&state={state}")

    response = client.get("/api/v1/integrations/status")
    assert response.status_code == 200
    statuses = response.json()
    assert len(statuses) == 1
    item = statuses[0]
    assert item["provider"] == "google-calendar"
    assert item["isActive"] is True
    # Ensure zero token fields in status schema
    assert "access_token" not in item
    assert "refresh_token" not in item


@patch("app.api.integrations.exchange_google_code")
def test_revoke_marks_inactive(mock_exchange, client):
    user_id = "demo-user-aarav"
    state = generate_oauth_state(user_id, "google-calendar")
    mock_exchange.return_value = TokenResponse(
        access_token="acc_token",
        refresh_token="ref_token",
        scopes=["https://www.googleapis.com/auth/calendar.readonly"],
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )

    client.get(f"/api/v1/integrations/google-calendar/callback?code=code_1&state={state}")

    # Delete connection
    del_resp = client.delete("/api/v1/integrations/google-calendar")
    assert del_resp.status_code == 204

    # Verify status reflects revoked
    status_resp = client.get("/api/v1/integrations/status")
    assert status_resp.status_code == 200
    statuses = status_resp.json()
    assert len(statuses) == 1
    assert statuses[0]["isActive"] is False
    assert statuses[0]["revokedAt"] is not None


def test_revoke_nonexistent_404(client):
    response = client.delete("/api/v1/integrations/google-calendar")
    assert response.status_code == 404


@patch("app.api.integrations.refresh_google_token")
def test_token_refresh_on_expiry(mock_refresh):
    db = TestingSessionLocal()
    repo = IntegrationRepository(db)
    user_id = "demo-user-aarav"

    # Insert connection expiring in 2 minutes (< 5 min threshold)
    expiring_time = datetime.now(timezone.utc) + timedelta(minutes=2)
    repo.upsert_connection(
        user_id=user_id,
        provider="google-calendar",
        access_token="old_access_token",
        refresh_token="valid_refresh_token",
        scopes=["calendar"],
        expires_at=expiring_time,
    )

    mock_refresh.return_value = TokenResponse(
        access_token="new_access_token_777",
        refresh_token="valid_refresh_token",
        scopes=["calendar"],
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )

    settings = get_settings()
    conn = ensure_fresh_token(user_id, "google-calendar", db, settings)
    assert conn is not None
    assert conn.access_token == "new_access_token_777"
    assert mock_refresh.called
    db.close()


@patch("app.api.integrations.refresh_google_token")
def test_refresh_failure_marks_revoked(mock_refresh):
    db = TestingSessionLocal()
    repo = IntegrationRepository(db)
    user_id = "demo-user-aarav"

    expiring_time = datetime.now(timezone.utc) + timedelta(minutes=2)
    repo.upsert_connection(
        user_id=user_id,
        provider="google-calendar",
        access_token="old_access_token",
        refresh_token="invalid_refresh_token",
        scopes=["calendar"],
        expires_at=expiring_time,
    )

    mock_refresh.side_effect = RuntimeError("Invalid Grant")

    settings = get_settings()
    with pytest.raises(Exception) as exc_info:
        ensure_fresh_token(user_id, "google-calendar", db, settings)

    assert "reconnect_required" in str(exc_info.value)

    # Verify connection was revoked in DB
    conn = repo.get_active_connection(user_id, "google-calendar")
    assert conn is None
    db.close()
