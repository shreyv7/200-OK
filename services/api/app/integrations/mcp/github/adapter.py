"""GitHub MCP Adapter (Fixture and Live). Owner: Person D. D4 (PRD §6, milestones.md M8).

Provides:
1. FixtureGithubAdapter: Maps simulated commit fixtures (simulated=True).
2. LiveGitHubAdapter & normalizers: Maps real live GitHub API commit/PR dicts (simulated=False).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict

from app.integrations.mcp.base import EvidenceAdapter
from app.schemas.evidence import EvidenceEvent, RawMCPPayload
from app.services.identity.scoring.constants import EVENT_WEIGHTS

_COMMIT_TYPE = "github_commit"
_PR_TYPE = "published_artifact"


def normalize_raw_github_commit(raw_commit: Dict[str, Any], user_id: str) -> EvidenceEvent:
    """Converts a live GitHub API commit dict/object to canonical EvidenceEvent with simulated=False."""
    sha = raw_commit.get("sha", str(uuid.uuid4()))
    commit_data = raw_commit.get("commit", {})
    message = commit_data.get("message", "Git commit")
    author_info = commit_data.get("author", {})
    date_str = author_info.get("date")

    if isinstance(date_str, str):
        timestamp = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    elif isinstance(date_str, datetime):
        timestamp = date_str
    else:
        timestamp = datetime.now(timezone.utc)

    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)

    repo_name = raw_commit.get("repository", {}).get("full_name", "")
    html_url = raw_commit.get("html_url", "")

    return EvidenceEvent(
        id=str(uuid.uuid4()),
        userId=user_id,
        timestamp=timestamp,
        source="github",
        type=_COMMIT_TYPE,
        category="creation",
        identityAttributeIds=[],
        value=1.0,
        baseWeight=EVENT_WEIGHTS.get(_COMMIT_TYPE, 4.0),
        metadata={
            "sha": sha,
            "message": message,
            "repo": repo_name,
            "url": html_url,
        },
        simulated=False,
    )


def normalize_raw_github_pr(raw_pr: Dict[str, Any], user_id: str) -> EvidenceEvent:
    """Converts a live merged GitHub PR dict to canonical EvidenceEvent (type=published_artifact, simulated=False)."""
    pr_id = str(raw_pr.get("id", uuid.uuid4()))
    title = raw_pr.get("title", "Merged Pull Request")
    merged_at_str = raw_pr.get("merged_at")

    if isinstance(merged_at_str, str):
        timestamp = datetime.fromisoformat(merged_at_str.replace("Z", "+00:00"))
    elif isinstance(merged_at_str, datetime):
        timestamp = merged_at_str
    else:
        timestamp = datetime.now(timezone.utc)

    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)

    repo_name = raw_pr.get("base", {}).get("repo", {}).get("full_name", "")
    html_url = raw_pr.get("html_url", "")

    return EvidenceEvent(
        id=str(uuid.uuid4()),
        userId=user_id,
        timestamp=timestamp,
        source="github",
        type=_PR_TYPE,
        category="creation",
        identityAttributeIds=[],
        value=1.0,
        baseWeight=EVENT_WEIGHTS.get(_PR_TYPE, 5.0),
        metadata={
            "pr_id": pr_id,
            "title": title,
            "repo": repo_name,
            "url": html_url,
        },
        simulated=False,
    )


class FixtureGithubAdapter(EvidenceAdapter):
    """Maps a commit-shaped fixture payload to a canonical EvidenceEvent (simulated=True)."""

    def normalize(self, payload: RawMCPPayload) -> EvidenceEvent:
        raw = payload.rawPayload
        timestamp = raw["timestamp"]
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)

        return EvidenceEvent(
            id=str(uuid.uuid4()),
            userId=raw["userId"],
            timestamp=timestamp,
            source="github",
            type=_COMMIT_TYPE,
            category="creation",
            identityAttributeIds=raw.get("identityAttributeIds", []),
            value=1.0,
            baseWeight=EVENT_WEIGHTS[_COMMIT_TYPE],
            metadata={"sha": raw.get("sha"), "message": raw.get("message")},
            simulated=True,
        )


class LiveGitHubAdapter(EvidenceAdapter):
    """Adapter for live GitHub events (simulated=False)."""

    def __init__(self, user_id: str) -> None:
        self._user_id = user_id

    def normalize(self, payload: RawMCPPayload) -> EvidenceEvent:
        raw = payload.rawPayload
        if "title" in raw or "merged_at" in raw:
            return normalize_raw_github_pr(raw, self._user_id)
        return normalize_raw_github_commit(raw, self._user_id)
