"""Support longer freeform Mirror Interview answers.

- Widen onboarding_turns.content to Text
- Add optional answer_kind (preset | freeform) for user turns

Revision ID: 0013
Revises: 0012
Create Date: 2026-08-02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0013"
down_revision: Union[str, None] = "0012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "onboarding_turns",
        "content",
        existing_type=sa.String(),
        type_=sa.Text(),
        existing_nullable=False,
    )
    op.add_column(
        "onboarding_turns",
        sa.Column("answer_kind", sa.String(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("onboarding_turns", "answer_kind")
    op.alter_column(
        "onboarding_turns",
        "content",
        existing_type=sa.Text(),
        type_=sa.String(),
        existing_nullable=False,
    )
