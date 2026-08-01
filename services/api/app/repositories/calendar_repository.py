"""Calendar leverage-event persistence. Owner: Backend. milestones.md M8 (F9)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select

from app.models.calendar_event import CalendarEventModel
from app.schemas.calendar import CalendarEventSchema


def _to_schema(row: CalendarEventModel) -> CalendarEventSchema:
    return CalendarEventSchema(
        id=row.id, title=row.title, eventTime=row.event_time, leverageTag=row.leverage_tag
    )


def create(db, user_id: str, title: str, event_time: datetime, leverage_tag: str | None = None) -> CalendarEventSchema:
    row = CalendarEventModel(user_id=user_id, title=title, event_time=event_time, leverage_tag=leverage_tag)
    db.add(row)
    db.commit()
    db.refresh(row)
    return _to_schema(row)


def list_upcoming(db, user_id: str) -> list[CalendarEventSchema]:
    stmt = (
        select(CalendarEventModel)
        .where(CalendarEventModel.user_id == user_id)
        .order_by(CalendarEventModel.event_time)
    )
    return [_to_schema(r) for r in db.scalars(stmt)]


def has_events(db, user_id: str) -> bool:
    stmt = select(CalendarEventModel.id).where(CalendarEventModel.user_id == user_id)
    return db.scalar(stmt) is not None
