"""Notion Sync Endpoint. Owner: Person D.

Exposes POST /api/v1/notion/sync to trigger on-demand activity sync (pages).
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
from app.services.notion.sync import NotionSyncService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notion", tags=["notion"])


class NotionSyncResponse(BaseModel):
    provider: str = "notion"
    synced: int
    message: str


@router.post("/sync", response_model=NotionSyncResponse, status_code=status.HTTP_202_ACCEPTED)
def trigger_notion_sync(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
    settings: Settings = Depends(get_settings),
) -> NotionSyncResponse:
    """Triggers an on-demand sync of recent Notion pages for the authenticated user.

    Returns HTTP 202 Accepted with count of new EvidenceEvents created.
    Raises HTTP 404 if user has no active Notion connection.
    """
    repo = IntegrationRepository(db)
    conn = repo.get_active_connection(user_id, "notion")

    if conn is None or not conn.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active Notion connection found. Please connect your Notion account first.",
        )

    try:
        count = NotionSyncService().sync_recent_pages(
            user_id=user_id,
            db=db,
            settings=settings,
        )
        return NotionSyncResponse(
            provider="notion",
            synced=count,
            message=f"Synced {count} new Notion evidence events",
        )
    except Exception as exc:
        logger.error("Notion sync failed for user %s: %s", user_id, exc)
        return NotionSyncResponse(
            provider="notion",
            synced=0,
            message=f"Notion sync completed with errors: {exc}",
        )
