"""D3: Add source_event_id to calendar_events for idempotent Google Calendar sync

Revision ID: 0010
Revises: 0009
Create Date: 2026-08-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0010"
down_revision: Union[str, None] = "0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "calendar_events",
        sa.Column("source_event_id", sa.String(length=255), nullable=True),
    )
    op.create_index(
        "ix_calendar_events_source_event_id",
        "calendar_events",
        ["user_id", "source_event_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_calendar_events_source_event_id", table_name="calendar_events")
    op.drop_column("calendar_events", "source_event_id")
