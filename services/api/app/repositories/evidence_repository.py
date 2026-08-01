"""Evidence persistence. Owner: Backend."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.evidence_event import EvidenceEventModel
from app.schemas.evidence import EvidenceEvent


def to_schema(row: EvidenceEventModel) -> EvidenceEvent:
    """Convert a persisted row back into the frozen EvidenceEvent contract.

    identityAttributeIds is never persisted (see app/services/identity's
    enrich_evidence_event) — it's re-derived on read, not stored, so this
    always returns an empty list here by design, not an oversight.
    """
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


def get_by_dedupe_hash(db: Session, dedupe_hash: str) -> EvidenceEventModel | None:
    stmt = select(EvidenceEventModel).where(
        EvidenceEventModel.dedupe_hash == dedupe_hash
    )
    return db.scalar(stmt)


def create_if_not_exists(
    db: Session, event: EvidenceEvent, dedupe_hash: str
) -> tuple[EvidenceEventModel, bool]:
    """Insert `event` unless `dedupe_hash` already exists. Returns (row, created)."""
    existing = get_by_dedupe_hash(db, dedupe_hash)
    if existing is not None:
        return existing, False

    row = EvidenceEventModel(
        id=event.id,
        user_id=event.userId,
        timestamp=event.timestamp,
        source=event.source,
        type=event.type,
        category=event.category,
        value=event.value,
        base_weight=event.baseWeight,
        event_metadata=event.metadata,
        simulated=event.simulated,
        dedupe_hash=dedupe_hash,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row, True


def list_window(
    db: Session,
    user_id: str,
    since: datetime | None = None,
    until: datetime | None = None,
    limit: int = 100,
) -> list[EvidenceEventModel]:
    stmt = select(EvidenceEventModel).where(EvidenceEventModel.user_id == user_id)
    if since is not None:
        stmt = stmt.where(EvidenceEventModel.timestamp >= since)
    if until is not None:
        stmt = stmt.where(EvidenceEventModel.timestamp <= until)
    stmt = stmt.order_by(EvidenceEventModel.timestamp).limit(limit)
    return list(db.scalars(stmt))
