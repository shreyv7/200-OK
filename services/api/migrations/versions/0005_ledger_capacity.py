"""ledger_entries, intervention_budgets tables + interventions.variants_json

Revision ID: 0005
Revises: 0004
Create Date: 2026-08-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "interventions",
        sa.Column("variants_json", sa.JSON(), nullable=False, server_default="{}"),
    )

    op.create_table(
        "ledger_entries",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("hypothesis_id", sa.String(), nullable=False),
        sa.Column("hypothesis_family", sa.String(), nullable=False),
        sa.Column("action", sa.String(), nullable=False),
        sa.Column("verdict", sa.String(), nullable=False, server_default="pending"),
        sa.Column("unlearning_triggered", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("lens_weight_adjustment", sa.JSON(), nullable=True),
        sa.Column("note", sa.String(), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_ledger_entries_user_id", "ledger_entries", ["user_id"])
    op.create_index("ix_ledger_entries_hypothesis_id", "ledger_entries", ["hypothesis_id"])
    op.create_index("ix_ledger_entries_hypothesis_family", "ledger_entries", ["hypothesis_family"])

    op.create_table(
        "intervention_budgets",
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.id"), primary_key=True),
        sa.Column("interventions_today", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("budget_date", sa.Date(), nullable=False),
        sa.Column("last_intervention_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("intervention_budgets")
    op.drop_index("ix_ledger_entries_hypothesis_family", table_name="ledger_entries")
    op.drop_index("ix_ledger_entries_hypothesis_id", table_name="ledger_entries")
    op.drop_index("ix_ledger_entries_user_id", table_name="ledger_entries")
    op.drop_table("ledger_entries")
    op.drop_column("interventions", "variants_json")
