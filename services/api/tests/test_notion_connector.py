"""Tests for Notion Connector — adapter, sync service, and sync endpoint. Owner: Person D."""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.core.db import get_db
from app.integrations.mcp.notion.adapter import (
    FixtureNotionAdapter,
    LiveNotionAdapter,
    normalize_raw_notion_page,
    normalize_raw_notion_page_edit,
)
from app.main import app
from app.models.base import Base
from app.repositories import evidence_repository
from app.repositories.integration_repository import IntegrationRepository
from app.schemas.evidence import RawMCPPayload
from app.services.notion.sync import NotionSyncService
from tests.conftest import ensure_user

TEST_DATABASE_URL = "sqlite:///./test_notion_connector.db"
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


def _make_raw_page(
    page_id: str = "page-123-uuid",
    title: str = "My Project Blueprint",
    created_time: str | None = None,
    last_edited_time: str | None = None,
) -> Dict[str, Any]:
    now_iso = datetime.now(timezone.utc).isoformat()
    c_time = created_time or now_iso
    e_time = last_edited_time or c_time

    return {
        "id": page_id,
        "created_time": c_time,
        "last_edited_time": e_time,
        "url": f"https://www.notion.so/{page_id}",
        "parent": {"type": "workspace"},
        "properties": {
            "title": {
                "id": "title",
                "type": "title",
                "title": [{"plain_text": title}],
            }
        },
    }


def test_normalize_created_page_simulated_false():
    """Live Notion page creation events must have simulated=False, source=notion, category=creation."""
    raw = _make_raw_page(page_id="page_999", title="System Architecture Notes")
    ev = normalize_raw_notion_page(raw, "user-aarav")

    assert ev.simulated is False
    assert ev.source == "notion"
    assert ev.type == "notion_page_created"
    assert ev.category == "creation"
    assert ev.baseWeight == 3.0
    assert ev.userId == "user-aarav"


def test_normalize_edited_page_type():
    """Live Notion page edit events must have type=notion_page_edited, baseWeight=1.5, simulated=False."""
    c_time = "2026-07-01T10:00:00.000Z"
    e_time = "2026-07-05T14:30:00.000Z"
    raw = _make_raw_page(page_id="page_888", title="Updated Strategy Doc", created_time=c_time, last_edited_time=e_time)
    ev = normalize_raw_notion_page_edit(raw, "user-aarav")

    assert ev.simulated is False
    assert ev.source == "notion"
    assert ev.type == "notion_page_edited"
    assert ev.category == "creation"
    assert ev.baseWeight == 1.5
    assert ev.userId == "user-aarav"


def test_normalize_page_metadata_preserved():
    """Page ID, title, url, parent_type must be preserved in metadata."""
    raw = _make_raw_page(page_id="page_meta_001", title="Deep Work Log")
    ev = normalize_raw_notion_page(raw, "user-aarav")

    assert ev.metadata["notion_page_id"] == "page_meta_001"
    assert ev.metadata["title"] == "Deep Work Log"
    assert ev.metadata["url"] == "https://www.notion.so/page_meta_001"
    assert ev.metadata["parent_type"] == "workspace"


def test_fixture_adapter_simulated_true():
    """FixtureNotionAdapter must map payloads to simulated=True events."""
    adapter = FixtureNotionAdapter()
    payload = RawMCPPayload(
        sourceProvider="notion",
        rawPayload={
            "userId": "user-aarav",
            "notion_page_id": "page_fix_1",
            "title": "Simulated Note",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )
    ev = adapter.normalize(payload)
    assert ev.simulated is True
    assert ev.source == "notion"
    assert ev.metadata["title"] == "Simulated Note"


def test_sync_returns_zero_if_no_connection():
    """Sync should return 0 and skip API calls if user has no active Notion connection."""
    db = TestingSessionLocal()
    settings = get_settings()

    with patch.object(NotionSyncService, "_fetch_pages") as mock_fetch:
        service = NotionSyncService()
        result = service.sync_recent_pages("user-no-notion", db, settings)

    assert result == 0
    mock_fetch.assert_not_called()
    db.close()


def test_sync_creates_evidence_events_from_pages():
    """With an active Notion connection, sync ingests real pages as EvidenceEvents."""
    db = TestingSessionLocal()
    ensure_user(db, "demo-user-aarav")
    repo = IntegrationRepository(db)
    user_id = "demo-user-aarav"

    repo.upsert_connection(
        user_id=user_id,
        provider="notion",
        access_token="mock_notion_token",
        refresh_token=None,
        scopes=["read_content"],
    )

    mock_pages = [
        _make_raw_page(page_id="page_1", title="Page One"),
        _make_raw_page(page_id="page_2", title="Page Two"),
    ]

    settings = get_settings()
    with patch.object(NotionSyncService, "_fetch_pages", return_value=mock_pages):
        service = NotionSyncService()
        new_count = service.sync_recent_pages(user_id, db, settings)

    assert new_count == 2

    rows = evidence_repository.list_window(db, user_id, limit=50)
    notion_rows = [r for r in rows if r.source == "notion"]
    assert len(notion_rows) == 2
    assert all(r.simulated is False for r in notion_rows)
    db.close()


def test_sync_is_idempotent():
    """Syncing the same Notion activity twice should ingest 0 new events on second run."""
    db = TestingSessionLocal()
    ensure_user(db, "demo-user-aarav")
    repo = IntegrationRepository(db)
    user_id = "demo-user-aarav"

    repo.upsert_connection(
        user_id=user_id,
        provider="notion",
        access_token="mock_notion_token",
        scopes=["read_content"],
    )

    mock_pages = [_make_raw_page(page_id="page_idem_01", title="Idempotent Page")]

    settings = get_settings()
    with patch.object(NotionSyncService, "_fetch_pages", return_value=mock_pages):
        service = NotionSyncService()
        new1 = service.sync_recent_pages(user_id, db, settings)
        new2 = service.sync_recent_pages(user_id, db, settings)

    assert new1 == 1
    assert new2 == 0  # Deduplication hash prevents duplicate rows
    db.close()


def test_sync_endpoint_returns_202(client):
    """POST /api/v1/notion/sync with active connection returns 202 Accepted and synced count."""
    db = TestingSessionLocal()
    ensure_user(db, "demo-user-aarav")
    repo = IntegrationRepository(db)
    user_id = "demo-user-aarav"

    repo.upsert_connection(
        user_id=user_id,
        provider="notion",
        access_token="mock_notion_token",
        scopes=["read_content"],
    )
    db.close()

    mock_pages = [_make_raw_page(page_id="page_ep_01", title="Endpoint Page")]

    with patch.object(NotionSyncService, "_fetch_pages", return_value=mock_pages):
        response = client.post("/api/v1/notion/sync")

    assert response.status_code == 202
    data = response.json()
    assert data["provider"] == "notion"
    assert data["synced"] == 1


def test_sync_endpoint_returns_404_if_not_connected(client):
    """POST /api/v1/notion/sync without active Notion connection returns 404 Not Found."""
    response = client.post("/api/v1/notion/sync")
    assert response.status_code == 404
    assert "No active Notion connection found" in response.json()["detail"]
