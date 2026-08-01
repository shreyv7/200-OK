"""GitHub Sync Endpoint. Owner: Person D. D4 (PRD §6, milestones.md M8).

Exposes POST /api/v1/github/sync to trigger on-demand activity sync (commits/PRs).
Used directly by front-end action buttons and periodic background Celery workers.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.di import get_current_user_id, get_db
from app.repositories.integration_repository import IntegrationRepository
from app.services.github.sync import GitHubSyncService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/github", tags=["github"])


class GitHubSyncResponse(BaseModel):
    provider: str = "github"
    synced: int
    message: str


@router.post("/sync", response_model=GitHubSyncResponse, status_code=status.HTTP_202_ACCEPTED)
def trigger_github_sync(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
    settings: Settings = Depends(get_settings),
) -> GitHubSyncResponse:
    """Triggers an on-demand sync of recent GitHub commits and PRs for the authenticated user.

    Returns HTTP 202 Accepted with count of new EvidenceEvents created.
    Raises HTTP 404 if user has no active GitHub connection.
    """
    repo = IntegrationRepository(db)
    conn = repo.get_active_connection(user_id, "github")

    if conn is None or not conn.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active GitHub connection found. Please connect your GitHub account first.",
        )

    try:
        count = GitHubSyncService().sync_recent_activity(
            user_id=user_id,
            db=db,
            settings=settings,
        )
        return GitHubSyncResponse(
            provider="github",
            synced=count,
            message=f"Synced {count} new GitHub evidence events",
        )
    except Exception as exc:
        logger.error("GitHub sync failed for user %s: %s", user_id, exc)
        return GitHubSyncResponse(
            provider="github",
            synced=0,
            message=f"GitHub sync completed with errors: {exc}",
        )
