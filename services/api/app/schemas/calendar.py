"""Calendar leverage-moment contract. Owner: Backend. milestones.md M8 (F9, P2)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class CalendarEventSchema(BaseModel):
    id: str
    title: str
    eventTime: datetime
    leverageTag: str | None = None
