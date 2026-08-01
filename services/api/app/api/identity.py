"""Identity read endpoint. Owner: Backend. milestones.md M2.

Write path (onboarding confirm/edit) is M3 scope — this milestone only
needs the read side so the dashboard has something to bind to.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.di import get_current_user_id, get_db
from app.repositories import twin_repository
from app.schemas.identity import DeclaredSelf

router = APIRouter(tags=["identity"])


@router.get("/identity", response_model=DeclaredSelf)
def get_identity(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
) -> DeclaredSelf:
    declared_self = twin_repository.get_active_declared_self(db, user_id)
    if declared_self is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No confirmed identity yet — complete onboarding first.",
        )
    return declared_self
