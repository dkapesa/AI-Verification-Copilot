"""create ai_reviews table

Revision ID: xxxx_create_ai_reviews_table
Revises: dbc06134de8d
Create Date: 2026-03-10
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "xxxx_create_ai_reviews_table"
down_revision = "dbc06134de8d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ai_reviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("decision", sa.String(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("reasons", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "recommended_next_steps",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "aggregated_signals",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("reasoning_summary", sa.Text(), nullable=True),
        sa.Column("model_provider", sa.String(), nullable=True),
        sa.Column("model_name", sa.String(), nullable=True),
        sa.Column("prompt_version", sa.String(), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_ai_reviews_case_id"), "ai_reviews", ["case_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_ai_reviews_case_id"), table_name="ai_reviews")
    op.drop_table("ai_reviews")