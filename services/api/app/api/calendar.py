"""Calendar plan-view endpoint. Owner: Backend. F9 (prd.md, P2), milestones.md M8."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.di import get_current_user_id, get_db
from app.repositories import calendar_repository
from app.schemas.calendar import CalendarEventSchema

router = APIRouter(tags=["calendar"])


@router.get("/calendar/plan-view", response_model=list[CalendarEventSchema])
def get_plan_view(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
) -> list[CalendarEventSchema]:
    return calendar_repository.list_upcoming(db, user_id)
