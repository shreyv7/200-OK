"""Identity Stack endpoints. Owner: Backend. F5 (prd.md), milestones.md M4."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.di import get_current_user_id, get_db, get_llm_provider, get_search_provider
from app.providers.llm.base import LLMProvider
from app.providers.search.base import SearchProvider
from app.repositories import intervention_repository
from app.schemas.stack import IdentityStack, InterventionVariant
from app.services.curation import stack_orchestration
from app.services.curation.trigger_refresh import enqueue_tier2_stack_refresh
from app.services.rate_limiter import check_rate_limit

router = APIRouter(tags=["stack"])


@router.post("/stack/refresh", status_code=status.HTTP_202_ACCEPTED)
def refresh_stack(
    user_id: str = Depends(get_current_user_id),
) -> dict[str, str]:
    """Kicks off a Tier-2 curation cycle (never blocks — F4 feed-morph requirement)."""
    check_rate_limit("stack_refresh", user_id, limit=5, window_seconds=10)
    enqueue_tier2_stack_refresh(user_id)
    return {"status": "refreshing"}


@router.get("/stack/active", response_model=IdentityStack)
def get_active_stack(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
    search_provider: SearchProvider = Depends(get_search_provider),
    llm_provider: LLMProvider = Depends(get_llm_provider),
) -> IdentityStack:
    row = intervention_repository.get_active(db, user_id)
    if row is None:
        # Sync cold-start refresh only when the user already has a confirmed twin.
        # Never seed Aarav attributes here (A5).
        stack = stack_orchestration.refresh_stack(db, user_id, search_provider, llm_provider)
        if stack is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active stack yet — complete onboarding, then call POST /stack/refresh.",
            )
        return stack
    return intervention_repository.to_stack(row)


@router.get("/stack/variants", response_model=dict[str, InterventionVariant])
def get_stack_variants(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
) -> dict[str, InterventionVariant]:
    """full/light/micro variants sharing the active hypothesisId (F6 Capacity Slider)."""
    row = intervention_repository.get_active(db, user_id)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active stack yet — call POST /stack/refresh first.",
        )
    return intervention_repository.to_variants(row)
