"""Intervention budget persistence. Owner: Backend. milestones.md M5 (F6 Guardian)."""

from __future__ import annotations

from datetime import date, datetime

from app.models.intervention_budget import InterventionBudgetModel


def get_or_create(db, user_id: str) -> InterventionBudgetModel:
    row = db.get(InterventionBudgetModel, user_id)
    if row is None:
        row = InterventionBudgetModel(user_id=user_id, interventions_today=0, budget_date=date.today())
        db.add(row)
        db.commit()
        db.refresh(row)
        return row

    if row.budget_date != date.today():
        row.budget_date = date.today()
        row.interventions_today = 0
        db.commit()
        db.refresh(row)
    return row


def record_intervention_delivered(db, user_id: str) -> InterventionBudgetModel:
    row = get_or_create(db, user_id)
    row.interventions_today += 1
    row.last_intervention_at = datetime.utcnow()
    db.commit()
    db.refresh(row)
    return row
