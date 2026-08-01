"""Agent run persistence. Owner: Backend. milestones.md M7."""

from __future__ import annotations

from app.models.agent_run import AgentRunModel


def create(db, user_id: str, run_type: str, result: dict) -> AgentRunModel:
    row = AgentRunModel(user_id=user_id, type=run_type, result_json=result)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
