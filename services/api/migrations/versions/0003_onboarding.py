"""onboarding_sessions and onboarding_turns tables

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "onboarding_sessions",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="in_progress"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_onboarding_sessions_user_id", "onboarding_sessions", ["user_id"])

    op.create_table(
        "onboarding_turns",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column(
            "session_id", sa.String(), sa.ForeignKey("onboarding_sessions.id"), nullable=False
        ),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("content", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_onboarding_turns_session_id", "onboarding_turns", ["session_id"])


def downgrade() -> None:
    op.drop_index("ix_onboarding_turns_session_id", table_name="onboarding_turns")
    op.drop_table("onboarding_turns")
    op.drop_index("ix_onboarding_sessions_user_id", table_name="onboarding_sessions")
    op.drop_table("onboarding_sessions")
