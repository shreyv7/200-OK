"""LLM usage/budget table. Owner: Backend. docs/work.md B5.

Mirrors the intervention_budgets pattern (app/models/intervention_budget.py,
milestones.md M5): one row per user, reset when the day rolls over.
"""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class LLMUsageBudgetModel(Base):
    __tablename__ = "llm_usage_budgets"

    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), primary_key=True)
    calls_today: Mapped[int] = mapped_column(Integer, default=0)
    tokens_today: Mapped[int] = mapped_column(Integer, default=0)
    budget_date: Mapped[date] = mapped_column(Date, default=date.today)
    last_call_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
