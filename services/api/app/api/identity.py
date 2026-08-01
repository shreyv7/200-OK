"""Identity read/edit endpoints. Owner: Backend. milestones.md M2/M3."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.di import get_current_user_id, get_db
from app.repositories import twin_repository
from app.repositories.twin_repository import WeightSumError
from app.schemas.identity import DeclaredSelf
from app.schemas.onboarding import IdentityPatchRequest

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


@router.patch("/identity", response_model=DeclaredSelf)
def patch_identity(
    request: IdentityPatchRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
) -> DeclaredSelf:
    """Edit the unconfirmed draft (from onboarding), optionally confirming it.

    Never touches an already-active (confirmed) Declared Self — only a
    draft can be edited; confirming only promotes the current draft
    (milestones.md M3 merge gate 3).
    """
    draft = twin_repository.upsert_draft(db, user_id, request.attributes)
    if not request.confirm:
        return draft

    try:
        return twin_repository.confirm_draft(db, user_id)
    except WeightSumError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
