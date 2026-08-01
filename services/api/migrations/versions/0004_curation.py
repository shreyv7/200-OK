"""resource_cache and interventions tables

Revision ID: 0004
Revises: 0003
Create Date: 2026-08-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "resource_cache",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("query_hash", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("url", sa.String(), nullable=False),
        sa.Column("extract", sa.String(), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("badge", sa.String(), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_resource_cache_query_hash", "resource_cache", ["query_hash"])

    op.create_table(
        "interventions",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("hypothesis_id", sa.String(), nullable=False),
        sa.Column("stack_json", sa.JSON(), nullable=False),
        sa.Column("verdict", sa.String(), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_interventions_user_id", "interventions", ["user_id"])
    op.create_index("ix_interventions_hypothesis_id", "interventions", ["hypothesis_id"])


def downgrade() -> None:
    op.drop_index("ix_interventions_hypothesis_id", table_name="interventions")
    op.drop_index("ix_interventions_user_id", table_name="interventions")
    op.drop_table("interventions")
    op.drop_index("ix_resource_cache_query_hash", table_name="resource_cache")
    op.drop_table("resource_cache")
