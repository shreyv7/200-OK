"""Calendar leverage-moment table. Owner: Backend / Person D. milestones.md M8 (F9, P2)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class CalendarEventModel(Base):
    __tablename__ = "calendar_events"
    __table_args__ = (
        # Unique per user + Google Calendar event ID for idempotent re-sync
        UniqueConstraint("user_id", "source_event_id", name="uq_calendar_user_source_event"),
        Index("ix_calendar_events_source_event_id", "user_id", "source_event_id", unique=True),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String)
    event_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    leverage_tag: Mapped[str | None] = mapped_column(String, nullable=True)
    # Google Calendar event ID — None for seeded/fixture rows
    source_event_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

