"""kpi_snapshots table

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "kpi_snapshots",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("gap_score", sa.Integer(), nullable=False),
        sa.Column("alignment", sa.Integer(), nullable=False),
        sa.Column("create_consume_ratio", sa.Float(), nullable=False),
        sa.Column("create_points", sa.Float(), nullable=False),
        sa.Column("consume_points", sa.Float(), nullable=False),
        sa.Column("drift_points", sa.Float(), nullable=False),
        sa.Column("consistency", sa.Float(), nullable=False),
        sa.Column("momentum", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("per_attribute", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("computed_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_kpi_snapshots_user_id", "kpi_snapshots", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_kpi_snapshots_user_id", table_name="kpi_snapshots")
    op.drop_table("kpi_snapshots")
