"""EvidenceEvent table. Owner: Backend. Real ingest endpoint lands in M1."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class EvidenceEventModel(Base):
    __tablename__ = "evidence_events"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    source: Mapped[str] = mapped_column(String)
    type: Mapped[str] = mapped_column(String)
    category: Mapped[str] = mapped_column(String)
    value: Mapped[float] = mapped_column(Float)
    base_weight: Mapped[float] = mapped_column(Float)
    event_metadata: Mapped[dict] = mapped_column(JSON, default=dict)
    simulated: Mapped[bool] = mapped_column(Boolean, default=False)
    dedupe_hash: Mapped[str] = mapped_column(String, unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
