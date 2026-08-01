"""Identity Stack endpoints. Owner: Backend. F5 (prd.md), milestones.md M4."""

from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.core.di import get_current_user_id, get_db, get_llm_provider, get_search_provider
from app.providers.llm.base import LLMProvider
from app.providers.search.base import SearchProvider
from app.repositories import intervention_repository
from app.schemas.stack import IdentityStack, InterventionVariant
from app.services.curation import stack_orchestration

router = APIRouter(tags=["stack"])


def _run_refresh(user_id: str, search_provider: SearchProvider, llm_provider: LLMProvider) -> None:
    # BackgroundTasks run after the response is sent, once the request's
    # `Depends(get_db)` session has already been torn down — must open a
    # fresh session here, not reuse the request-scoped one.
    db = SessionLocal()
    try:
        stack_orchestration.refresh_stack(db, user_id, search_provider, llm_provider)
    finally:
        db.close()


@router.post("/stack/refresh", status_code=status.HTTP_202_ACCEPTED)
def refresh_stack(
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_current_user_id),
    search_provider: SearchProvider = Depends(get_search_provider),
    llm_provider: LLMProvider = Depends(get_llm_provider),
) -> dict[str, str]:
    """Kicks off a Tier-2 curation cycle (never blocks — F4 feed-morph requirement)."""
    background_tasks.add_task(_run_refresh, user_id, search_provider, llm_provider)
    return {"status": "refreshing"}


@router.get("/stack/active", response_model=IdentityStack)
def get_active_stack(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
) -> IdentityStack:
    row = intervention_repository.get_active(db, user_id)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active stack yet — call POST /stack/refresh first.",
        )
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
