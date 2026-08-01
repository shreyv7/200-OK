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
