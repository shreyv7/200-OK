"""initial schema: users, evidence_events, twin_versions

Revision ID: 0001
Revises:
Create Date: 2026-08-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("clerk_subject", sa.String(), nullable=True, unique=True),
        sa.Column("capacity", sa.Float(), nullable=False, server_default="100.0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "evidence_events",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("base_weight", sa.Float(), nullable=False),
        sa.Column("event_metadata", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("simulated", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("dedupe_hash", sa.String(), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_evidence_events_user_id", "evidence_events", ["user_id"])
    op.create_index("ix_evidence_events_dedupe_hash", "evidence_events", ["dedupe_hash"], unique=True)

    op.create_table(
        "twin_versions",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("attributes", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_twin_versions_user_id", "twin_versions", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_twin_versions_user_id", table_name="twin_versions")
    op.drop_table("twin_versions")
    op.drop_index("ix_evidence_events_dedupe_hash", table_name="evidence_events")
    op.drop_index("ix_evidence_events_user_id", table_name="evidence_events")
    op.drop_table("evidence_events")
    op.drop_table("users")
