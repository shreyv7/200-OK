"""Mirror Interview onboarding endpoint. Owner: Backend. F1 (prd.md), milestones.md M3."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.di import get_budgeted_llm_provider, get_current_user_id, get_db
from app.providers.llm.base import LLMProvider
from app.schemas.onboarding import OnboardingPersona, OnboardingTurnRequest, OnboardingTurnResponse
from app.services.identity import onboarding_orchestration
from app.services.identity.onboarding_personas import list_personas

router = APIRouter(tags=["onboarding"])


@router.get("/identity/onboarding/personas", response_model=list[OnboardingPersona])
def get_onboarding_personas() -> list[OnboardingPersona]:
    return list_personas()


@router.post("/identity/onboarding", response_model=OnboardingTurnResponse)
def onboarding_turn(
    request: OnboardingTurnRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
    llm_provider: LLMProvider = Depends(get_budgeted_llm_provider),
) -> OnboardingTurnResponse:
    try:
        return onboarding_orchestration.advance_turn(
            db, llm_provider, user_id, request.sessionId, request.message, request.personaId
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
