"""KPI snapshot table. Owner: Backend. Persists AIA's deterministic Gap/KPI output."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class KPISnapshotModel(Base):
    __tablename__ = "kpi_snapshots"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), index=True)
    gap_score: Mapped[int] = mapped_column(Integer)
    alignment: Mapped[int] = mapped_column(Integer)
    create_consume_ratio: Mapped[float] = mapped_column(Float)
    create_points: Mapped[float] = mapped_column(Float)
    consume_points: Mapped[float] = mapped_column(Float)
    drift_points: Mapped[float] = mapped_column(Float)
    consistency: Mapped[float] = mapped_column(Float)
    momentum: Mapped[int] = mapped_column(Integer, default=0)
    per_attribute: Mapped[list] = mapped_column(JSON, default=list)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
