"""Intervention/hypothesis shell table. Owner: Backend. milestones.md M4.

Verdict-pending shell only — dismiss/complete/unlearning transitions are
M5's Trust Ledger (app/schemas/ledger.py), not this table.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class InterventionModel(Base):
    __tablename__ = "interventions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), index=True)
    hypothesis_id: Mapped[str] = mapped_column(String, index=True)
    stack_json: Mapped[dict] = mapped_column(JSON)
    verdict: Mapped[str] = mapped_column(String, default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
