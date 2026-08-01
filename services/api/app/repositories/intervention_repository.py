"""Intervention/hypothesis shell persistence. Owner: Backend. milestones.md M4/M5."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.intervention import InterventionModel
from app.schemas.stack import IdentityStack, InterventionVariant


def create(
    db: Session, user_id: str, stack: IdentityStack, variants: dict[str, dict] | None = None
) -> InterventionModel:
    row = InterventionModel(
        user_id=user_id,
        hypothesis_id=stack.hypothesisId,
        stack_json=stack.model_dump(mode="json"),
        variants_json=variants or {},
        verdict="pending",
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def get_active(db: Session, user_id: str) -> InterventionModel | None:
    """Most recently created intervention for user_id — the active stack."""
    stmt = (
        select(InterventionModel)
        .where(InterventionModel.user_id == user_id)
        .order_by(InterventionModel.created_at.desc())
    )
    return db.scalars(stmt).first()


def to_stack(row: InterventionModel) -> IdentityStack:
    return IdentityStack.model_validate(row.stack_json)


def to_variants(row: InterventionModel) -> dict[str, InterventionVariant]:
    return {
        intensity: InterventionVariant.model_validate(data)
        for intensity, data in (row.variants_json or {}).items()
    }
