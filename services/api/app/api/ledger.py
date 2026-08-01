"""Trust Ledger endpoints. Owner: Backend. F7 (prd.md), milestones.md M5.

Threshold check (3 dismissals in 14 days -> failed + unlearning) is
implemented here as a deterministic rule — same category as M3's
weight-sum enforcement, not LLM arithmetic (guidelines.md §9.1).
AIS's own M5 reflection module may duplicate/replace this once it
lands; reconcile then, don't block the demo path on it now.
"""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.di import get_current_user_id, get_db
from app.repositories import ledger_repository
from app.schemas.ledger import LedgerAction, LedgerEntry
from app.services.identity.scoring.constants import (
    DISMISSAL_FAILURE_THRESHOLD,
    DISMISSAL_WINDOW_DAYS,
)

router = APIRouter(tags=["ledger"])

_UNLEARNING_LENS_ADJUSTMENT = {"media": -0.4}  # prd.md §7 F7 worked example


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


@router.post("/ledger/record", response_model=LedgerEntry)
def record_ledger_entry(
    request: LedgerRecordRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
) -> LedgerEntry:
    verdict: Literal["worked", "failed", "pending"] = "pending"
    unlearning = False
    lens_adjustment = None

    if request.action == "dismissed":
        dismissal_count = ledger_repository.count_recent_dismissals(
            db, request.hypothesisFamily, DISMISSAL_WINDOW_DAYS
        )
        # +1 for the dismissal being recorded right now.
        if dismissal_count + 1 >= DISMISSAL_FAILURE_THRESHOLD:
            verdict = "failed"
            unlearning = True
            lens_adjustment = _UNLEARNING_LENS_ADJUSTMENT
    elif request.action == "completed":
        verdict = "worked"

    return ledger_repository.record(
        db,
        user_id=user_id,
        hypothesis_id=request.hypothesisId,
        hypothesis_family=request.hypothesisFamily,
        action=request.action,
        verdict=verdict,
        unlearning_triggered=unlearning,
        lens_weight_adjustment=lens_adjustment,
    )
