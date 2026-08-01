"""Intervention budget table. Owner: Backend. milestones.md M5 (F6 Guardian)."""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class InterventionBudgetModel(Base):
    __tablename__ = "intervention_budgets"

    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), primary_key=True)
    interventions_today: Mapped[int] = mapped_column(Integer, default=0)
    budget_date: Mapped[date] = mapped_column(Date, default=date.today)
    last_intervention_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
