"""Dashboard summary endpoint. Owner: Backend. F3 (prd.md), milestones.md M2.

Realtime strategy: 2s client-side polling of this endpoint (prd.md §11 /
techstack.md §3 explicitly prefer this over WebSockets for the MVP). This
endpoint does no LLM/retrieval work — safe to poll on a Tier-0 budget.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.di import get_current_user_id, get_db
from app.models.user import User
from app.repositories import twin_repository
from app.schemas.dashboard import DashboardSummary
from app.services.identity import orchestration

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard/summary", response_model=DashboardSummary)
def get_dashboard_summary(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
) -> DashboardSummary:
    declared_self = twin_repository.get_active_declared_self(db, user_id)
    if declared_self is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No confirmed identity yet — complete onboarding first.",
        )

    result = orchestration.recompute_and_persist(db, user_id)
    if result is None:
        # Can't happen given the check above, but keeps the type checker honest.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Identity not found.")

    user = db.get(User, user_id)
    capacity = user.capacity if user is not None else 100.0

    return DashboardSummary(
        userId=user_id,
        declaredSelf=declared_self,
        gap=result.gap,
        bottleneck=result.bottleneck,
        capacity=capacity,
    )
