"""B5 (docs/work.md): llm_usage_budgets table for per-user daily LLM
call cap + token usage logging.

Revision ID: 0009
Revises: 0008
Create Date: 2026-08-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0009"
down_revision: Union[str, None] = "0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "llm_usage_budgets",
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.id"), primary_key=True),
        sa.Column("calls_today", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("tokens_today", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("budget_date", sa.Date(), nullable=False),
        sa.Column("last_call_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("llm_usage_budgets")
