"""Declared Self / Twin version persistence. Owner: Backend; shape owned by AIA."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.twin_version import TwinVersion
from app.schemas.identity import DeclaredSelf, IdentityAttribute


def _row_to_schema(row: TwinVersion) -> DeclaredSelf:
    return DeclaredSelf(
        id=row.id,
        userId=row.user_id,
        version=row.version,
        attributes=[IdentityAttribute.model_validate(a) for a in row.attributes],
        createdAt=row.created_at,
        confirmedAt=row.confirmed_at,
    )


def get_active_declared_self(db: Session, user_id: str) -> DeclaredSelf | None:
    """Latest confirmed TwinVersion for user_id, or None if never confirmed."""
    stmt = (
        select(TwinVersion)
        .where(TwinVersion.user_id == user_id, TwinVersion.confirmed_at.is_not(None))
        .order_by(TwinVersion.version.desc())
    )
    row = db.scalars(stmt).first()
    return _row_to_schema(row) if row is not None else None


def create_version(
    db: Session,
    user_id: str,
    version: int,
    attributes: list[IdentityAttribute],
    confirmed_at: datetime | None = None,
) -> DeclaredSelf:
    row = TwinVersion(
        user_id=user_id,
        version=version,
        attributes=[a.model_dump(mode="json") for a in attributes],
        confirmed_at=confirmed_at,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _row_to_schema(row)


def _get_draft_row(db: Session, user_id: str) -> TwinVersion | None:
    stmt = (
        select(TwinVersion)
        .where(TwinVersion.user_id == user_id, TwinVersion.confirmed_at.is_(None))
        .order_by(TwinVersion.version.desc())
    )
    return db.scalars(stmt).first()


def get_draft(db: Session, user_id: str) -> DeclaredSelf | None:
    """Latest unconfirmed TwinVersion for user_id — the onboarding draft."""
    row = _get_draft_row(db, user_id)
    return _row_to_schema(row) if row is not None else None


def upsert_draft(
    db: Session, user_id: str, attributes: list[IdentityAttribute]
) -> DeclaredSelf:
    """Create the draft if none exists yet, else overwrite its attributes in place.

    Never creates a second unconfirmed row — onboarding's draft is a single
    slot per user until confirmed.
    """
    existing = _get_draft_row(db, user_id)
    if existing is not None:
        existing.attributes = [a.model_dump(mode="json") for a in attributes]
        db.commit()
        db.refresh(existing)
        return _row_to_schema(existing)

    next_version = db.scalar(
        select(TwinVersion.version)
        .where(TwinVersion.user_id == user_id)
        .order_by(TwinVersion.version.desc())
    )
    return create_version(
        db,
        user_id=user_id,
        version=(next_version or 0) + 1,
        attributes=attributes,
        confirmed_at=None,
    )


class WeightSumError(ValueError):
    """Raised when a draft's attribute weights don't sum to 1.0 on confirm."""


def confirm_draft(db: Session, user_id: str, weight_tolerance: float = 1e-6) -> DeclaredSelf:
    """Promote the current draft to the active confirmed version.

    Enforces sum(w_i) == 1.0 (milestones.md M3) — rejects rather than
    silently rescaling, since that would hide a real extraction/edit bug.
    """
    row = _get_draft_row(db, user_id)
    if row is None:
        raise ValueError(f"No draft identity to confirm for user {user_id}")

    total_weight = sum(a["weight"] for a in row.attributes)
    if abs(total_weight - 1.0) > weight_tolerance:
        raise WeightSumError(
            f"Attribute weights sum to {total_weight}, expected 1.0"
        )

    row.confirmed_at = datetime.utcnow()
    db.commit()
    db.refresh(row)
    return _row_to_schema(row)
