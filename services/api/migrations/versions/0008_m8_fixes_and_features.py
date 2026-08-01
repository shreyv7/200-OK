"""M8: reshape identity_evolution_proposals to match AIA's real schema,
add calendar_events table

Revision ID: 0008
Revises: 0007
Create Date: 2026-08-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0008"
down_revision: Union[str, None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # M7's table shape (proposed_attributes/cited_evidence_ids/rationale)
    # never shipped past this hackathon's own dev branch — safe to drop
    # and recreate matching AIA's real generation output shape instead of
    # a column-by-column migration.
    op.drop_table("identity_evolution_proposals")
    op.create_table(
        "identity_evolution_proposals",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("declared_self_version", sa.Integer(), nullable=False),
        sa.Column("proposed_changes", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("supporting_evidence_ids", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("narrative", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_identity_evolution_proposals_user_id", "identity_evolution_proposals", ["user_id"])

    op.create_table(
        "calendar_events",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("event_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("leverage_tag", sa.String(), nullable=True),
    )
    op.create_index("ix_calendar_events_user_id", "calendar_events", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_calendar_events_user_id", table_name="calendar_events")
    op.drop_table("calendar_events")

    op.drop_index("ix_identity_evolution_proposals_user_id", table_name="identity_evolution_proposals")
    op.drop_table("identity_evolution_proposals")
    op.create_table(
        "identity_evolution_proposals",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("proposed_attributes", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("cited_evidence_ids", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("rationale", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
