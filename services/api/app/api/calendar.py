"""Calendar plan-view endpoint. Owner: Backend / Person D. F9 (prd.md, P2), milestones.md M8.

D3: Updated to trigger an on-demand Google Calendar sync before serving rows.
Falls back gracefully to seeded/existing rows when no connection or on API failure.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.di import get_current_user_id, get_db
from app.repositories import calendar_repository
from app.schemas.calendar import CalendarEventSchema
from app.services.calendar.sync import GoogleCalendarSyncService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["calendar"])


@router.get("/calendar/plan-view", response_model=list[CalendarEventSchema])
def get_plan_view(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
    settings: Settings = Depends(get_settings),
) -> list[CalendarEventSchema]:
    """Returns upcoming calendar events for plan-view (F9).

    Attempts an on-demand Google Calendar sync first. On no connection or any
    network/auth error, falls through silently to return existing DB rows.
    """
    try:
        GoogleCalendarSyncService().sync_upcoming_events(
            user_id=user_id,
            db=db,
            settings=settings,
        )
    except Exception as exc:
        logger.warning(
            "Calendar plan-view sync skipped for user %s: %s", user_id, exc
        )

    return calendar_repository.list_upcoming(db, user_id)

