"""Tests for Google Calendar Connector — adapter, sync service, and plan-view endpoint. Owner: Person D."""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.core.db import get_db
from app.core.oauth_state import generate_oauth_state
from app.integrations.mcp.calendar.adapter import (
    CalendarEventAdapter,
    normalize_raw_google_event,
)
from app.main import app
from app.models.base import Base
from app.repositories.calendar_repository import upsert_from_google_event
from app.repositories.integration_repository import IntegrationRepository
from app.repositories import evidence_repository
from app.services.calendar.sync import GoogleCalendarSyncService
from app.schemas.evidence import RawMCPPayload

TEST_DATABASE_URL = "sqlite:///./test_calendar_connector.db"
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


def _make_google_event(
    event_id: str = "gcal_evt_001",
    title: str = "College presentation",
    start_datetime: str | None = None,
    start_date: str | None = None,
) -> Dict[str, Any]:
    """Creates a fake Google Calendar API event dict."""
    start: Dict[str, Any] = {}
    if start_datetime:
        start["dateTime"] = start_datetime
    elif start_date:
        start["date"] = start_date
    else:
        start["dateTime"] = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()

    return {
        "id": event_id,
        "summary": title,
        "start": start,
        "organizer": {"email": "test@example.com"},
    }


def test_normalize_all_day_event():
    """All-day events (start.date) should use noon UTC as representative time."""
    raw = _make_google_event(event_id="evt_all_day", title="Conference Day", start_date="2026-08-10")
    ev = normalize_raw_google_event(raw, "user-123")

    assert ev.timestamp.hour == 12
    assert ev.timestamp.tzinfo is not None
    assert ev.timestamp.date() == datetime(2026, 8, 10).date()
    assert ev.userId == "user-123"
    assert ev.source == "google_calendar"


def test_normalize_datetime_event():
    """Timed events (start.dateTime) preserve the exact timestamp."""
    specific_time = "2026-08-15T09:30:00+05:30"
    raw = _make_google_event(event_id="evt_timed", title="Morning Standup", start_datetime=specific_time)
    ev = normalize_raw_google_event(raw, "user-456")

    assert ev.metadata["google_event_id"] == "evt_timed"
    assert ev.metadata["title"] == "Morning Standup"
    # Timestamp should be parsed (with tz)
    assert ev.timestamp.tzinfo is not None


def test_normalize_simulated_false():
    """All calendar events from Google must have simulated=False and category=creation."""
    raw = _make_google_event()
    ev = normalize_raw_google_event(raw, "user-789")

    assert ev.simulated is False
    assert ev.category == "creation"
    assert ev.source == "google_calendar"
    assert ev.type == "attended_experience"
    assert ev.baseWeight == 4.0


def test_sync_returns_zero_if_no_connection():
    """Sync should return 0 and skip API call if no active google-calendar connection."""
    db = TestingSessionLocal()
    settings = get_settings()

    with patch.object(GoogleCalendarSyncService, "_fetch_events") as mock_fetch:
        service = GoogleCalendarSyncService()
        result = service.sync_upcoming_events("user-no-connection", db, settings)

    assert result == 0
    mock_fetch.assert_not_called()
    db.close()


def test_sync_creates_calendar_rows():
    """With a connected user and mocked Google API, sync should create calendar_events rows."""
    db = TestingSessionLocal()
    repo = IntegrationRepository(db)
    user_id = "demo-user-aarav"

    # Set up active connection
    repo.upsert_connection(
        user_id=user_id,
        provider="google-calendar",
        access_token="mock_access_token",
        refresh_token="mock_refresh_token",
        scopes=["https://www.googleapis.com/auth/calendar.readonly"],
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )

    mock_events = [
        _make_google_event("evt_001", "College presentation", start_datetime=(datetime.now(timezone.utc) + timedelta(days=3)).isoformat()),
        _make_google_event("evt_002", "Project demo day", start_datetime=(datetime.now(timezone.utc) + timedelta(days=7)).isoformat()),
    ]

    settings = get_settings()
    with patch.object(GoogleCalendarSyncService, "_fetch_events", return_value=mock_events):
        service = GoogleCalendarSyncService()
        new_count = service.sync_upcoming_events(user_id, db, settings)

    assert new_count == 2

    from sqlalchemy import select
    from app.models.calendar_event import CalendarEventModel
    rows = db.execute(select(CalendarEventModel).where(CalendarEventModel.user_id == user_id)).scalars().all()
    assert len(rows) == 2
    titles = {r.title for r in rows}
    assert "College presentation" in titles
    db.close()


def test_sync_ingests_evidence_events():
    """Sync should create EvidenceEvent rows with simulated=False in evidence_events table."""
    db = TestingSessionLocal()
    repo = IntegrationRepository(db)
    user_id = "demo-user-aarav"

    repo.upsert_connection(
        user_id=user_id,
        provider="google-calendar",
        access_token="mock_access_token",
        refresh_token="mock_refresh_token",
        scopes=["https://www.googleapis.com/auth/calendar.readonly"],
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )

    mock_events = [
        _make_google_event("evt_003", "Tech Talk", start_datetime=(datetime.now(timezone.utc) + timedelta(days=5)).isoformat()),
    ]

    settings = get_settings()
    with patch.object(GoogleCalendarSyncService, "_fetch_events", return_value=mock_events):
        GoogleCalendarSyncService().sync_upcoming_events(user_id, db, settings)

    rows = evidence_repository.list_window(db, user_id, limit=50)
    calendar_rows = [r for r in rows if r.source == "google_calendar"]
    assert len(calendar_rows) == 1
    assert calendar_rows[0].simulated is False
    assert calendar_rows[0].type == "attended_experience"
    db.close()


def test_sync_is_idempotent():
    """Running sync twice with the same events should not duplicate calendar_events rows."""
    db = TestingSessionLocal()
    repo = IntegrationRepository(db)
    user_id = "demo-user-aarav"

    repo.upsert_connection(
        user_id=user_id,
        provider="google-calendar",
        access_token="mock_access_token",
        refresh_token="mock_refresh_token",
        scopes=["https://www.googleapis.com/auth/calendar.readonly"],
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )

    mock_events = [
        _make_google_event("evt_idem_001", "Idempotent Event", start_datetime=(datetime.now(timezone.utc) + timedelta(days=4)).isoformat()),
    ]

    settings = get_settings()
    with patch.object(GoogleCalendarSyncService, "_fetch_events", return_value=mock_events):
        new1 = GoogleCalendarSyncService().sync_upcoming_events(user_id, db, settings)
        new2 = GoogleCalendarSyncService().sync_upcoming_events(user_id, db, settings)

    assert new1 == 1
    assert new2 == 0  # idempotent — no new rows on second sync

    from sqlalchemy import select
    from app.models.calendar_event import CalendarEventModel
    rows = db.execute(select(CalendarEventModel).where(CalendarEventModel.user_id == user_id)).scalars().all()
    assert len(rows) == 1
    db.close()


def test_plan_view_returns_synced_events(client):
    """GET /calendar/plan-view should return real synced event titles from Google Calendar."""
    db = TestingSessionLocal()
    repo = IntegrationRepository(db)
    user_id = "demo-user-aarav"

    repo.upsert_connection(
        user_id=user_id,
        provider="google-calendar",
        access_token="mock_access_token",
        refresh_token="mock_refresh_token",
        scopes=["https://www.googleapis.com/auth/calendar.readonly"],
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    db.close()

    mock_events = [
        _make_google_event("evt_pv_001", "Live Keynote Speech", start_datetime=(datetime.now(timezone.utc) + timedelta(days=2)).isoformat()),
    ]

    with patch.object(GoogleCalendarSyncService, "_fetch_events", return_value=mock_events):
        response = client.get("/api/v1/calendar/plan-view")

    assert response.status_code == 200
    titles = [e["title"] for e in response.json()]
    assert "Live Keynote Speech" in titles


def test_plan_view_falls_back_to_seeded_on_no_connection(client):
    """With no google-calendar connection, plan-view returns seeded rows without error."""
    response = client.get("/api/v1/calendar/plan-view")
    assert response.status_code == 200
    # Returns a list (possibly empty — no seed in test DB, but no 500)
    assert isinstance(response.json(), list)


def test_plan_view_survives_google_api_failure(client):
    """Google API failure during sync should not cause a 500 — returns existing rows."""
    from googleapiclient.errors import HttpError
    import httplib2

    db = TestingSessionLocal()
    repo = IntegrationRepository(db)
    user_id = "demo-user-aarav"

    repo.upsert_connection(
        user_id=user_id,
        provider="google-calendar",
        access_token="invalid_access_token",
        refresh_token=None,
        scopes=["https://www.googleapis.com/auth/calendar.readonly"],
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    db.close()

    mock_http_error = HttpError(resp=httplib2.Response({"status": "403"}), content=b"Forbidden")

    with patch.object(GoogleCalendarSyncService, "_fetch_events", side_effect=mock_http_error):
        response = client.get("/api/v1/calendar/plan-view")

    assert response.status_code == 200
    assert isinstance(response.json(), list)
