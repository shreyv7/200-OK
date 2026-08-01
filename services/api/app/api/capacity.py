"""Capacity endpoint. Owner: Backend. F6 (prd.md), milestones.md M5.

Capacity change is itself a context/evidence event (not a side-channel
setting) per guidelines.md's "one evidence path" — but it must never
move the Gap score, so it's ingested with value=0.0 (AIA's gap.py uses
EvidenceEvent.value as the base weight override, so 0.0 means zero
contribution regardless of category/type classification).
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.di import get_current_user_id, get_db
from app.models.user import User
from app.schemas.evidence import EvidenceIngestRequest
from app.services.curation.trigger_refresh import enqueue_tier2_stack_refresh
from app.services.evidence import service as evidence_service

router = APIRouter(tags=["capacity"])


class CapacityUpdateRequest(BaseModel):
    value: float = Field(ge=0.0, le=100.0)


@router.patch("/capacity")
def set_capacity(
    request: CapacityUpdateRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
) -> dict[str, float]:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown user")

    user.capacity = request.value
    db.commit()

    context_event = EvidenceIngestRequest(
        userId=user_id,
        timestamp=datetime.utcnow(),
        source="trellis",
        type="capacity_set",
        category="reflection",
        value=0.0,
        baseWeight=0.0,
        metadata={"capacity": request.value},
        simulated=False,
    )
    evidence_service.ingest(db, context_event)
    enqueue_tier2_stack_refresh(user_id)

    return {"capacity": user.capacity}
