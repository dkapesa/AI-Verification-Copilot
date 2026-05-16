"""create human overrides table

Revision ID: 5f8336d829aa
Revises: xxxx_create_ai_reviews_table
Create Date: 2026-05-13 10:35:52.138122

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "5f8336d829aa"
down_revision: Union[str, Sequence[str], None] = "xxxx_create_ai_reviews_table"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "human_overrides",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("decision", sa.String(length=32), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("actor_type", sa.String(length=64), nullable=False, server_default="human"),
        sa.Column("original_ai_decision", sa.String(length=32), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_human_overrides_case_id"),
        "human_overrides",
        ["case_id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_human_overrides_decision"),
        "human_overrides",
        ["decision"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_human_overrides_decision"), table_name="human_overrides")
    op.drop_index(op.f("ix_human_overrides_case_id"), table_name="human_overrides")
    op.drop_table("human_overrides")