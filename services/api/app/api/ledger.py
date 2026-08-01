"""Trust Ledger endpoints. Owner: Backend. F7 (prd.md), milestones.md M5.

Threshold check (3 dismissals in 14 days -> failed + unlearning) is
implemented here as a deterministic rule — same category as M3's
weight-sum enforcement, not LLM arithmetic (guidelines.md §9.1).
AIS's own M5 reflection module may duplicate/replace this once it
lands; reconcile then, don't block the demo path on it now.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.di import get_current_user_id, get_db
from app.repositories import ledger_repository
from app.schemas.ledger import LedgerAction, LedgerEntry
from app.services.curation.trigger_refresh import enqueue_tier2_stack_refresh
from app.services.recommendation.reflection_ledger import process_ledger_action

router = APIRouter(tags=["ledger"])


class LedgerRecordRequest(BaseModel):
    hypothesisId: str
    hypothesisFamily: str
    action: LedgerAction


@router.get("/ledger", response_model=list[LedgerEntry])
def list_ledger(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
) -> list[LedgerEntry]:
    return ledger_repository.list_for_user(db, user_id)


@router.get("/ledger/lens-weights", response_model=dict[str, float])
def get_lens_weights(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
) -> dict[str, float]:
    return ledger_repository.get_lens_weights(db, user_id)


@router.get("/ledger/adaptations", response_model=list[LedgerEntry])
def list_adaptations(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
) -> list[LedgerEntry]:
    """System Unlearning / lens-adjustment entries — milestones.md M6 P1 view."""
    return ledger_repository.list_adaptations(db, user_id)


@router.post("/ledger/record", response_model=LedgerEntry)
def record_ledger_entry(
    request: LedgerRecordRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
) -> LedgerEntry:
    result = process_ledger_action(
        user_id,
        request.hypothesisId,
        request.hypothesisFamily,
        request.action,
        db=db,
    )
    if request.action in ("dismissed", "completed"):
        enqueue_tier2_stack_refresh(user_id)
    return result.ledger_entry
