"""Trust Ledger persistence. Owner: Backend. milestones.md M5."""

from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ledger_entry import LedgerEntryModel
from app.schemas.ledger import LedgerEntry


def _to_schema(row: LedgerEntryModel) -> LedgerEntry:
    return LedgerEntry(
        id=row.id,
        userId=row.user_id,
        hypothesisId=row.hypothesis_id,
        hypothesisFamily=row.hypothesis_family,
        action=row.action,
        verdict=row.verdict,
        timestamp=row.timestamp,
        unlearningTriggered=row.unlearning_triggered,
        lensWeightAdjustment=row.lens_weight_adjustment,
        note=row.note,
    )


def record(
    db: Session,
    user_id: str,
    hypothesis_id: str,
    hypothesis_family: str,
    action: str,
    verdict: str = "pending",
    unlearning_triggered: bool = False,
    lens_weight_adjustment: dict[str, float] | None = None,
    note: str | None = None,
    timestamp: datetime | None = None,
) -> LedgerEntry:
    row = LedgerEntryModel(
        user_id=user_id,
        hypothesis_id=hypothesis_id,
        hypothesis_family=hypothesis_family,
        action=action,
        verdict=verdict,
        unlearning_triggered=unlearning_triggered,
        lens_weight_adjustment=lens_weight_adjustment,
        note=note,
        timestamp=timestamp or datetime.utcnow(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _to_schema(row)


def list_for_user(db: Session, user_id: str) -> list[LedgerEntry]:
    stmt = (
        select(LedgerEntryModel)
        .where(LedgerEntryModel.user_id == user_id)
        .order_by(LedgerEntryModel.timestamp.desc())
    )
    return [_to_schema(r) for r in db.scalars(stmt)]


def get_lens_weights(db: Session, user_id: str) -> dict[str, float]:
    """Latest lensWeightAdjustment per lens key across this user's ledger
    history — cumulative isn't tracked yet (M5 scope: last-write-wins)."""
    stmt = (
        select(LedgerEntryModel)
        .where(LedgerEntryModel.user_id == user_id, LedgerEntryModel.lens_weight_adjustment.is_not(None))
        .order_by(LedgerEntryModel.timestamp.asc())
    )
    weights: dict[str, float] = {}
    for row in db.scalars(stmt):
        weights.update(row.lens_weight_adjustment or {})
    return weights


def list_adaptations(db: Session, user_id: str) -> list[LedgerEntry]:
    """Entries where System Unlearning fired or a lens weight was adjusted —
    the "adaptations" view of the full ledger history (milestones.md M6)."""
    stmt = (
        select(LedgerEntryModel)
        .where(
            LedgerEntryModel.user_id == user_id,
            (LedgerEntryModel.unlearning_triggered.is_(True))
            | (LedgerEntryModel.lens_weight_adjustment.is_not(None)),
        )
        .order_by(LedgerEntryModel.timestamp.desc())
    )
    return [_to_schema(r) for r in db.scalars(stmt)]


def count_recent_dismissals(
    db: Session, hypothesis_family: str, window_days: int
) -> int:
    cutoff = datetime.utcnow() - timedelta(days=window_days)
    stmt = select(LedgerEntryModel).where(
        LedgerEntryModel.hypothesis_family == hypothesis_family,
        LedgerEntryModel.action == "dismissed",
        LedgerEntryModel.timestamp >= cutoff,
    )
    return len(list(db.scalars(stmt)))
