"""Evidence ingest/list endpoints. Owner: Backend. F2 (prd.md), milestones.md M1."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.core.di import get_current_user_id, get_db
from app.models.evidence_event import EvidenceEventModel
from app.repositories import evidence_repository
from app.schemas.evidence import EvidenceEvent, EvidenceIngestRequest
from app.services.evidence import service as evidence_service

router = APIRouter(tags=["evidence"])


def _to_schema(row: EvidenceEventModel) -> EvidenceEvent:
    return EvidenceEvent(
        id=row.id,
        userId=row.user_id,
        timestamp=row.timestamp,
        source=row.source,
        type=row.type,
        category=row.category,
        identityAttributeIds=[],
        value=row.value,
        baseWeight=row.base_weight,
        metadata=row.event_metadata,
        simulated=row.simulated,
    )


@router.post("/evidence", response_model=EvidenceEvent)
def create_evidence(
    request: EvidenceIngestRequest,
    response: Response,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
) -> EvidenceEvent:
    # Attribute to the authenticated caller, not a client-supplied body field —
    # a client-controlled userId would let one caller write events for another.
    request = request.model_copy(update={"userId": user_id})
    row, created = evidence_service.ingest(db, request)
    response.status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
    return _to_schema(row)


@router.get("/evidence", response_model=list[EvidenceEvent])
def list_evidence(
    since: datetime | None = None,
    until: datetime | None = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
) -> list[EvidenceEvent]:
    rows = evidence_repository.list_window(
        db, user_id, since=since, until=until, limit=limit
    )
    return [_to_schema(row) for row in rows]
