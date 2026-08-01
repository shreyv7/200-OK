"""Evidence ingest orchestration. Owner: Backend.

Single evidence path per guidelines.md §9.2: every event — seeded, live,
or simulator-injected — passes through `ingest()`. No caller may write
directly to the repository/table.
"""

from __future__ import annotations

import hashlib
import uuid
from collections.abc import Callable
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.evidence_event import EvidenceEventModel
from app.repositories import evidence_repository
from app.schemas.evidence import EvidenceEvent, EvidenceIngestRequest

EvidenceCreatedListener = Callable[[EvidenceEventModel], None]

_listeners: list[EvidenceCreatedListener] = []


def on_evidence_created(listener: EvidenceCreatedListener) -> None:
    """Register a callback invoked once per newly persisted evidence event."""
    _listeners.append(listener)


def _emit_evidence_created(row: EvidenceEventModel) -> None:
    for listener in _listeners:
        listener(row)


def compute_dedupe_hash(
    user_id: str, source: str, type_: str, timestamp: datetime, value: float
) -> str:
    key = f"{user_id}|{source}|{type_}|{timestamp.isoformat()}|{value}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def request_from_event(event: EvidenceEvent) -> EvidenceIngestRequest:
    """Adapt a normalized EvidenceEvent (from an adapter) into an ingest request."""
    return EvidenceIngestRequest(
        userId=event.userId,
        timestamp=event.timestamp,
        source=event.source,
        type=event.type,
        category=event.category,
        identityAttributeIds=event.identityAttributeIds,
        value=event.value,
        baseWeight=event.baseWeight,
        metadata=event.metadata,
        simulated=event.simulated,
    )


def ingest(
    db: Session, request: EvidenceIngestRequest
) -> tuple[EvidenceEventModel, bool]:
    """Idempotently persist an evidence event and emit `evidence.created` if new."""
    dedupe_hash = compute_dedupe_hash(
        request.userId, request.source, request.type, request.timestamp, request.value
    )
    event = EvidenceEvent(
        id=str(uuid.uuid4()),
        userId=request.userId,
        timestamp=request.timestamp,
        source=request.source,
        type=request.type,
        category=request.category,
        identityAttributeIds=request.identityAttributeIds,
        value=request.value,
        baseWeight=request.baseWeight,
        metadata=request.metadata,
        simulated=request.simulated,
    )
    row, created = evidence_repository.create_if_not_exists(db, event, dedupe_hash)
    if created:
        _emit_evidence_created(row)
    return row, created
