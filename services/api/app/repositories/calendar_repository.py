"""Calendar leverage-event persistence. Owner: Backend. milestones.md M8 (F9)."""

from __future__ import annotations

from datetime import datetime
from typing import Optional, Tuple

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

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


def upsert_from_google_event(
    db,
    user_id: str,
    source_event_id: str,
    title: str,
    event_time: datetime,
    leverage_tag: Optional[str] = None,
) -> Tuple[CalendarEventSchema, bool]:
    """Upserts a Google Calendar event into calendar_events by (user_id, source_event_id).

    Returns (schema, created: bool). This is the dedup mechanism for idempotent syncs.
    """
    stmt = select(CalendarEventModel).where(
        CalendarEventModel.user_id == user_id,
        CalendarEventModel.source_event_id == source_event_id,
    )
    existing = db.execute(stmt).scalar_one_or_none()

    if existing is not None:
        # Update mutable fields in case event was edited in Google Calendar
        existing.title = title
        existing.event_time = event_time
        existing.leverage_tag = leverage_tag
        db.commit()
        db.refresh(existing)
        return _to_schema(existing), False

    row = CalendarEventModel(
        user_id=user_id,
        title=title,
        event_time=event_time,
        leverage_tag=leverage_tag,
        source_event_id=source_event_id,
    )
    db.add(row)
    try:
        db.commit()
        db.refresh(row)
        return _to_schema(row), True
    except IntegrityError:
        db.rollback()
        # Race condition: row inserted by concurrent request — fetch and return it
        existing = db.execute(stmt).scalar_one()
        return _to_schema(existing), False


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
