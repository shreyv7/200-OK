"""LLM usage/budget persistence. Owner: Backend. docs/work.md B5.

Mirrors budget_repository.py's (M5 intervention budget) get_or_create /
record_* shape.
"""

from __future__ import annotations

from datetime import date, datetime

from app.models.llm_usage_budget import LLMUsageBudgetModel


def get_or_create(db, user_id: str) -> LLMUsageBudgetModel:
    row = db.get(LLMUsageBudgetModel, user_id)
    if row is None:
        row = LLMUsageBudgetModel(user_id=user_id, calls_today=0, tokens_today=0, budget_date=date.today())
        db.add(row)
        db.commit()
        db.refresh(row)
        return row

    if row.budget_date != date.today():
        row.budget_date = date.today()
        row.calls_today = 0
        row.tokens_today = 0
        db.commit()
        db.refresh(row)
    return row


def record_call(db, user_id: str, total_tokens: int = 0) -> LLMUsageBudgetModel:
    row = get_or_create(db, user_id)
    row.calls_today += 1
    row.tokens_today += max(0, total_tokens)
    row.last_call_at = datetime.utcnow()
    db.commit()
    db.refresh(row)
    return row
