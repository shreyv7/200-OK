"""Agent run endpoint. Owner: Backend. F8/F11 (prd.md), milestones.md M7."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.di import get_current_user_id, get_db, get_llm_provider
from app.providers.llm.base import LLMProvider
from app.repositories import agent_run_repository
from app.schemas.agent_run import AgentRunRequest, AgentRunResult
from app.services.identity import agent_runs

router = APIRouter(tags=["agents"])


@router.post("/agents/runs", response_model=AgentRunResult)
def create_agent_run(
    request: AgentRunRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
    llm_provider: LLMProvider = Depends(get_llm_provider),
) -> AgentRunResult:
    weekly_report = None
    evolution_proposal = None

    if request.type == "weekly_report":
        weekly_report = agent_runs.generate_weekly_report(db, llm_provider, user_id)
        result_payload = weekly_report.model_dump(mode="json")
    else:
        evolution_proposal = agent_runs.generate_evolution_proposal(db, llm_provider, user_id)
        result_payload = evolution_proposal.model_dump(mode="json")

    row = agent_run_repository.create(db, user_id, request.type, result_payload)

    return AgentRunResult(
        runId=row.id,
        type=request.type,
        weeklyReport=weekly_report,
        evolutionProposal=evolution_proposal,
    )
