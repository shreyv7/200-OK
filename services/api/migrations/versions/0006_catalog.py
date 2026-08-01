"""growth_stories, tools, mentors catalog tables

Revision ID: 0006
Revises: 0005
Create Date: 2026-08-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "growth_stories",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("author", sa.String(), nullable=False),
        sa.Column("summary", sa.String(), nullable=False),
        sa.Column("outcome", sa.String(), nullable=False),
        sa.Column("identity_tags", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("stage_tags", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("bottleneck_tags", sa.JSON(), nullable=False, server_default="[]"),
    )

    op.create_table(
        "tools",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("url", sa.String(), nullable=False),
        sa.Column("starter_action", sa.String(), nullable=False),
        sa.Column("stage_tags", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("bottleneck_tags", sa.JSON(), nullable=False, server_default="[]"),
    )

    op.create_table(
        "mentors",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("journey", sa.String(), nullable=False),
        sa.Column("strengths", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("stage_tags", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("bottleneck_tags", sa.JSON(), nullable=False, server_default="[]"),
    )


def downgrade() -> None:
    op.drop_table("mentors")
    op.drop_table("tools")
    op.drop_table("growth_stories")
