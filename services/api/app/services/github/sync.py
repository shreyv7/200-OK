"""GitHub Sync Service. Owner: Person D. D4 (PRD §6, milestones.md M8).

Fetches recent commits and merged pull requests from GitHub API using the user's
OAuth access token (via D1 IntegrationRepository and D2 ensure_fresh_token),
normalizes them to EvidenceEvent records (simulated=False), and ingests them through
the single evidence pipeline.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any, Dict, List

from sqlalchemy.orm import Session

if TYPE_CHECKING:
    from app.core.config import Settings

logger = logging.getLogger(__name__)

_DEFAULT_DAYS_BACK = 30


class GitHubSyncService:
    """Syncs recent GitHub activity (commits and PRs) for a connected user.

    Designed to be triggered on-demand via POST /api/v1/github/sync and
    periodically via Celery worker/beat (Person C). All GitHub API interaction
    is isolated in helper methods for clean mocking in tests.
    """

    def sync_recent_activity(
        self,
        user_id: str,
        db: Session,
        settings: "Settings",
        days_back: int = _DEFAULT_DAYS_BACK,
    ) -> int:
        """Fetches and syncs recent commits and merged PRs for user_id.

        Returns the count of new EvidenceEvent rows created (deduped, so re-sync = 0).
        Returns 0 immediately if no active github connection exists.
        """
        from app.api.integrations import ensure_fresh_token
        from app.integrations.mcp.github.adapter import (
            normalize_raw_github_commit,
            normalize_raw_github_pr,
        )
        from app.services.evidence import service as evidence_service
        from app.services.evidence.service import request_from_event

        try:
            conn = ensure_fresh_token(user_id, "github", db, settings)
        except Exception as exc:
            logger.warning(
                "github token refresh failed for user %s, skipping sync: %s",
                user_id,
                exc,
            )
            return 0

        if conn is None or not conn.is_active:
            return 0

        since_dt = datetime.now(timezone.utc) - timedelta(days=days_back)

        try:
            raw_commits = self._fetch_commits(conn.access_token, since_dt)
        except Exception as exc:
            logger.warning("GitHub API commits fetch failed for user %s: %s", user_id, exc)
            raw_commits = []

        try:
            raw_prs = self._fetch_prs(conn.access_token, since_dt)
        except Exception as exc:
            logger.warning("GitHub API PRs fetch failed for user %s: %s", user_id, exc)
            raw_prs = []

        new_count = 0

        # Process commits
        for raw_c in raw_commits:
            ev = normalize_raw_github_commit(raw_c, user_id)
            req = request_from_event(ev)
            _, created = evidence_service.ingest(db, req)
            if created:
                new_count += 1

        # Process merged PRs
        for raw_pr in raw_prs:
            ev = normalize_raw_github_pr(raw_pr, user_id)
            req = request_from_event(ev)
            _, created = evidence_service.ingest(db, req)
            if created:
                new_count += 1

        return new_count

    def _fetch_commits(self, access_token: str, since_dt: datetime) -> List[Dict[str, Any]]:
        """Calls GitHub API via PyGithub to list recent commits by the authenticated user.

        Isolated for test mocking via `patch.object(GitHubSyncService, "_fetch_commits")`.
        """
        from github import Github

        g = Github(access_token)
        user = g.get_user()

        commits: List[Dict[str, Any]] = []

        # Get repos owned or accessible by user
        for repo in user.get_repos(type="owner"):
            try:
                repo_commits = repo.get_commits(author=user.login, since=since_dt)
                for c in repo_commits[:20]:  # Cap per repo
                    commits.append({
                        "sha": c.sha,
                        "commit": {
                            "message": c.commit.message,
                            "author": {"date": c.commit.author.date.isoformat() if c.commit.author else since_dt.isoformat()},
                        },
                        "repository": {"full_name": repo.full_name},
                        "html_url": c.html_url,
                    })
            except Exception as e:
                logger.debug("Failed fetching commits for repo %s: %s", repo.full_name, e)
                continue

        return commits

    def _fetch_prs(self, access_token: str, since_dt: datetime) -> List[Dict[str, Any]]:
        """Calls GitHub API via PyGithub to list merged PRs by the authenticated user.

        Isolated for test mocking via `patch.object(GitHubSyncService, "_fetch_prs")`.
        """
        from github import Github

        g = Github(access_token)
        user = g.get_user()

        prs: List[Dict[str, Any]] = []
        try:
            query = f"author:{user.login} is:pr is:merged merged:>{since_dt.strftime('%Y-%m-%d')}"
            issues = g.search_issues(query)
            for issue in issues[:10]:
                pr = issue.as_pull_request()
                prs.append({
                    "id": str(pr.id),
                    "title": pr.title,
                    "merged_at": pr.merged_at.isoformat() if pr.merged_at else since_dt.isoformat(),
                    "base": {"repo": {"full_name": pr.base.repo.full_name if pr.base and pr.base.repo else ""}},
                    "html_url": pr.html_url,
                })
        except Exception as e:
            logger.debug("Failed searching PRs for user %s: %s", user.login, e)

        return prs
