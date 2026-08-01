"""Identity read/edit endpoints. Owner: Backend. milestones.md M2/M3/M7/M8."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.di import get_current_user_id, get_db
from app.repositories import evolution_repository, twin_repository
from app.repositories.twin_repository import WeightSumError
from app.schemas.identity import DeclaredSelf
from app.schemas.onboarding import IdentityPatchRequest
from app.services.curation.trigger_refresh import enqueue_tier2_stack_refresh
from app.services.identity.agent_runs import apply_proposed_changes

router = APIRouter(tags=["identity"])


class EvolutionStatusResponse(BaseModel):
    proposalId: str
    status: str


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
        confirmed = twin_repository.confirm_draft(db, user_id)
    except WeightSumError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    enqueue_tier2_stack_refresh(user_id)
    return confirmed


@router.post("/identity/evolution/{proposal_id}/accept", response_model=DeclaredSelf)
def accept_evolution(
    proposal_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
) -> DeclaredSelf:
    """Accept -> versioned Twin vN; Gap uses the new version from here on
    (milestones.md M7 merge gate 2). Applies the proposal's add/remove/
    reweight diff against the CURRENT confirmed attributes (M8 fix — the
    original version replaced the whole attribute list, silently dropping
    anything the proposal didn't mention)."""
    found = evolution_repository.get_for_user(db, proposal_id, user_id)
    if found is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown proposal")
    row, proposal = found
    if row.status != "pending":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Proposal already {row.status}")

    current = twin_repository.get_active_declared_self(db, user_id)
    current_attributes = current.attributes if current is not None else []
    merged_attributes = apply_proposed_changes(current_attributes, proposal.proposedChanges)

    declared_self = twin_repository.create_confirmed_version(db, user_id, merged_attributes)
    evolution_repository.set_status(db, row, "accepted")
    enqueue_tier2_stack_refresh(user_id)
    return declared_self


@router.post("/identity/evolution/{proposal_id}/reject", response_model=EvolutionStatusResponse)
def reject_evolution(
    proposal_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
) -> EvolutionStatusResponse:
    """Reject -> no mutation whatsoever to identity data (merge gate 2)."""
    found = evolution_repository.get_for_user(db, proposal_id, user_id)
    if found is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown proposal")
    row, _proposal = found
    if row.status != "pending":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Proposal already {row.status}")

    updated = evolution_repository.set_status(db, row, "rejected")
    return EvolutionStatusResponse(proposalId=updated.proposalId, status="rejected")
