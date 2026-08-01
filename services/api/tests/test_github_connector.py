"""Tests for GitHub Connector — adapter, sync service, and sync endpoint. Owner: Person D."""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.core.db import get_db
from app.integrations.mcp.github.adapter import (
    LiveGitHubAdapter,
    normalize_raw_github_commit,
    normalize_raw_github_pr,
)
from app.main import app
from app.models.base import Base
from app.repositories import evidence_repository
from app.repositories.integration_repository import IntegrationRepository
from app.schemas.evidence import RawMCPPayload
from app.services.github.sync import GitHubSyncService
from tests.conftest import ensure_user

TEST_DATABASE_URL = "sqlite:///./test_github_connector.db"
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


def _make_raw_commit(
    sha: str = "abc123def456",
    message: str = "feat(auth): add OAuth flow",
    repo: str = "shreyv7/200-OK",
    commit_date: str | None = None,
) -> Dict[str, Any]:
    return {
        "sha": sha,
        "commit": {
            "message": message,
            "author": {
                "date": commit_date or datetime.now(timezone.utc).isoformat(),
            },
        },
        "repository": {"full_name": repo},
        "html_url": f"https://github.com/{repo}/commit/{sha}",
    }


def _make_raw_pr(
    pr_id: str = "pr_101",
    title: str = "feat: add GitHub connector",
    repo: str = "shreyv7/200-OK",
    merged_at: str | None = None,
) -> Dict[str, Any]:
    return {
        "id": pr_id,
        "title": title,
        "merged_at": merged_at or datetime.now(timezone.utc).isoformat(),
        "base": {"repo": {"full_name": repo}},
        "html_url": f"https://github.com/{repo}/pull/{pr_id}",
    }


def test_normalize_commit_simulated_false():
    """Live GitHub commit events must have simulated=False, source=github, category=creation."""
    raw = _make_raw_commit(sha="sha_999", message="fix: resolve memory leak")
    ev = normalize_raw_github_commit(raw, "user-aarav")

    assert ev.simulated is False
    assert ev.source == "github"
    assert ev.type == "github_commit"
    assert ev.category == "creation"
    assert ev.baseWeight == 4.0
    assert ev.userId == "user-aarav"


def test_normalize_commit_metadata():
    """SHA, message, repo, and URL must be preserved in metadata."""
    raw = _make_raw_commit(sha="sha_meta_001", message="docs: update README", repo="org/repo-a")
    ev = normalize_raw_github_commit(raw, "user-aarav")

    assert ev.metadata["sha"] == "sha_meta_001"
    assert ev.metadata["message"] == "docs: update README"
    assert ev.metadata["repo"] == "org/repo-a"
    assert "https://github.com/org/repo-a/commit/sha_meta_001" in ev.metadata["url"]


def test_normalize_pr_merged_uses_published_artifact_type():
    """Merged PRs should use published_artifact type with baseWeight 5.0 and simulated=False."""
    raw = _make_raw_pr(pr_id="pr_777", title="feat: major release v1.0")
    ev = normalize_raw_github_pr(raw, "user-aarav")

    assert ev.simulated is False
    assert ev.source == "github"
    assert ev.type == "published_artifact"
    assert ev.category == "creation"
    assert ev.baseWeight == 5.0
    assert ev.metadata["title"] == "feat: major release v1.0"


def test_sync_returns_zero_if_no_connection():
    """Sync should return 0 and skip API calls if user has no active GitHub connection."""
    db = TestingSessionLocal()
    settings = get_settings()

    with patch.object(GitHubSyncService, "_fetch_commits") as mock_commits:
        with patch.object(GitHubSyncService, "_fetch_prs") as mock_prs:
            service = GitHubSyncService()
            result = service.sync_recent_activity("user-no-github", db, settings)

    assert result == 0
    mock_commits.assert_not_called()
    mock_prs.assert_not_called()
    db.close()


def test_sync_creates_evidence_events_from_commits():
    """With an active GitHub connection, sync ingests real commits as EvidenceEvents."""
    db = TestingSessionLocal()
    ensure_user(db, "demo-user-aarav")
    repo = IntegrationRepository(db)
    user_id = "demo-user-aarav"

    repo.upsert_connection(
        user_id=user_id,
        provider="github",
        access_token="mock_github_token",
        refresh_token=None,
        scopes=["repo", "read:user"],
    )

    mock_commits = [
        _make_raw_commit(sha="sha_1", message="Commit 1"),
        _make_raw_commit(sha="sha_2", message="Commit 2"),
    ]

    settings = get_settings()
    with patch.object(GitHubSyncService, "_fetch_commits", return_value=mock_commits):
        with patch.object(GitHubSyncService, "_fetch_prs", return_value=[]):
            service = GitHubSyncService()
            new_count = service.sync_recent_activity(user_id, db, settings)

    assert new_count == 2

    rows = evidence_repository.list_window(db, user_id, limit=50)
    gh_rows = [r for r in rows if r.source == "github"]
    assert len(gh_rows) == 2
    assert all(r.simulated is False for r in gh_rows)
    db.close()


def test_sync_creates_evidence_from_merged_pr():
    """Sync ingests merged PRs as published_artifact EvidenceEvents."""
    db = TestingSessionLocal()
    ensure_user(db, "demo-user-aarav")
    repo = IntegrationRepository(db)
    user_id = "demo-user-aarav"

    repo.upsert_connection(
        user_id=user_id,
        provider="github",
        access_token="mock_github_token",
        scopes=["repo"],
    )

    mock_prs = [_make_raw_pr(pr_id="pr_1", title="Merged feature PR")]

    settings = get_settings()
    with patch.object(GitHubSyncService, "_fetch_commits", return_value=[]):
        with patch.object(GitHubSyncService, "_fetch_prs", return_value=mock_prs):
            service = GitHubSyncService()
            new_count = service.sync_recent_activity(user_id, db, settings)

    assert new_count == 1

    rows = evidence_repository.list_window(db, user_id, limit=50)
    gh_rows = [r for r in rows if r.source == "github"]
    assert len(gh_rows) == 1
    assert gh_rows[0].type == "published_artifact"
    assert gh_rows[0].simulated is False
    db.close()


def test_sync_is_idempotent():
    """Syncing the same GitHub activity twice should ingest 0 new events on second run."""
    db = TestingSessionLocal()
    ensure_user(db, "demo-user-aarav")
    repo = IntegrationRepository(db)
    user_id = "demo-user-aarav"

    repo.upsert_connection(
        user_id=user_id,
        provider="github",
        access_token="mock_github_token",
        scopes=["repo"],
    )

    mock_commits = [_make_raw_commit(sha="sha_idem_01", message="Idempotent commit")]

    settings = get_settings()
    with patch.object(GitHubSyncService, "_fetch_commits", return_value=mock_commits):
        with patch.object(GitHubSyncService, "_fetch_prs", return_value=[]):
            service = GitHubSyncService()
            new1 = service.sync_recent_activity(user_id, db, settings)
            new2 = service.sync_recent_activity(user_id, db, settings)

    assert new1 == 1
    assert new2 == 0  # Deduplication hash prevents duplicate rows
    db.close()


def test_sync_endpoint_returns_202(client):
    """POST /api/v1/github/sync with active connection returns 202 Accepted and synced count."""
    db = TestingSessionLocal()
    ensure_user(db, "demo-user-aarav")
    repo = IntegrationRepository(db)
    user_id = "demo-user-aarav"

    repo.upsert_connection(
        user_id=user_id,
        provider="github",
        access_token="mock_github_token",
        scopes=["repo"],
    )
    db.close()

    mock_commits = [_make_raw_commit(sha="sha_ep_01", message="Endpoint commit")]

    with patch.object(GitHubSyncService, "_fetch_commits", return_value=mock_commits):
        with patch.object(GitHubSyncService, "_fetch_prs", return_value=[]):
            response = client.post("/api/v1/github/sync")

    assert response.status_code == 202
    data = response.json()
    assert data["provider"] == "github"
    assert data["synced"] == 1


def test_sync_endpoint_returns_404_if_not_connected(client):
    """POST /api/v1/github/sync without active GitHub connection returns 404 Not Found."""
    response = client.post("/api/v1/github/sync")
    assert response.status_code == 404
    assert "No active GitHub connection found" in response.json()["detail"]
