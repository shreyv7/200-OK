"""Trust Ledger table. Owner: Backend. milestones.md M5. Mirrors app/schemas/ledger.py."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class LedgerEntryModel(Base):
    __tablename__ = "ledger_entries"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), index=True)
    hypothesis_id: Mapped[str] = mapped_column(String, index=True)
    hypothesis_family: Mapped[str] = mapped_column(String, index=True)
    action: Mapped[str] = mapped_column(String)
    verdict: Mapped[str] = mapped_column(String, default="pending")
    unlearning_triggered: Mapped[bool] = mapped_column(Boolean, default=False)
    lens_weight_adjustment: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    note: Mapped[str | None] = mapped_column(String, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
