"""Evidence ingest/list endpoints. Owner: Backend. F2 (prd.md), milestones.md M1."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.core.di import get_current_user_id, get_db
from app.repositories import evidence_repository
from app.schemas.evidence import EvidenceEvent, EvidenceIngestBody, EvidenceIngestRequest
from app.services.evidence import service as evidence_service
from app.services.rate_limiter import check_rate_limit

router = APIRouter(tags=["evidence"])


@router.post("/evidence", response_model=EvidenceEvent)
def create_evidence(
    body: EvidenceIngestBody,
    response: Response,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
) -> EvidenceEvent:
    check_rate_limit("evidence", user_id, limit=10, window_seconds=10)
    # userId is never accepted from the client — always the authenticated caller (A3).
    request = EvidenceIngestRequest(userId=user_id, **body.model_dump())
    row, created = evidence_service.ingest(db, request)
    response.status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
    return evidence_repository.to_schema(row)


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
    return [evidence_repository.to_schema(row) for row in rows]
