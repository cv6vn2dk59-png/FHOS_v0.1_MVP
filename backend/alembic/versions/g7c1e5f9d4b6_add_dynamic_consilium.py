"""add dynamic consilium over hypothesis graph

Revision ID: g7c1e5f9d4b6
Revises: f6b0d4e8c3a5
"""
from alembic import op
import sqlalchemy as sa

revision = "g7c1e5f9d4b6"
down_revision = "f6b0d4e8c3a5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "dynamic_consilium_sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("case_id", sa.String(64), nullable=False),
        sa.Column("branch_ids", sa.JSON(), nullable=False),
        sa.Column("role_codes", sa.JSON(), nullable=False),
        sa.Column("consensus_snapshot", sa.JSON(), nullable=False),
        sa.Column("violations", sa.JSON(), nullable=False),
        sa.Column("warnings", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_dynamic_consilium_sessions_case_id", "dynamic_consilium_sessions", ["case_id"])
    op.create_table(
        "dynamic_consilium_reviews",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("session_id", sa.Integer(), sa.ForeignKey("dynamic_consilium_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role_code", sa.String(80), nullable=False),
        sa.Column("branch_id", sa.String(128), nullable=False),
        sa.Column("position", sa.String(40), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("evidence_ids", sa.JSON(), nullable=False),
        sa.Column("requested_evidence_ids", sa.JSON(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("provenance", sa.JSON(), nullable=False),
    )
    op.create_index("ix_dynamic_consilium_reviews_session_id", "dynamic_consilium_reviews", ["session_id"])
    op.create_index("ix_dynamic_consilium_reviews_branch_id", "dynamic_consilium_reviews", ["branch_id"])


def downgrade() -> None:
    op.drop_index("ix_dynamic_consilium_reviews_branch_id", table_name="dynamic_consilium_reviews")
    op.drop_index("ix_dynamic_consilium_reviews_session_id", table_name="dynamic_consilium_reviews")
    op.drop_table("dynamic_consilium_reviews")
    op.drop_index("ix_dynamic_consilium_sessions_case_id", table_name="dynamic_consilium_sessions")
    op.drop_table("dynamic_consilium_sessions")
