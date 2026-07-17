"""add multi ai consilium runs

Revision ID: m4d8a2c6f1e3
Revises: k1b5f9a3d7c2
"""
from alembic import op
import sqlalchemy as sa

revision = "m4d8a2c6f1e3"
down_revision = "k1b5f9a3d7c2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "multi_ai_consilium_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("run_id", sa.String(length=128), nullable=False),
        sa.Column("case_id", sa.String(length=64), nullable=False),
        sa.Column("mode", sa.String(length=20), nullable=False),
        sa.Column("execution_mode", sa.String(length=20), nullable=False),
        sa.Column("requested_provider_codes", sa.JSON(), nullable=False),
        sa.Column("successful_provider_codes", sa.JSON(), nullable=False),
        sa.Column("failed_provider_codes", sa.JSON(), nullable=False),
        sa.Column("case_package", sa.JSON(), nullable=False),
        sa.Column("clinical_graph_snapshot", sa.JSON(), nullable=False),
        sa.Column("comparison_snapshot", sa.JSON(), nullable=False),
        sa.Column("devil_review_snapshot", sa.JSON(), nullable=False),
        sa.Column("consensus_snapshot", sa.JSON(), nullable=False),
        sa.Column("warnings", sa.JSON(), nullable=False),
        sa.Column("limitations", sa.JSON(), nullable=False),
        sa.Column("violations", sa.JSON(), nullable=False),
        sa.Column("clinical_graph_version", sa.String(length=50), nullable=False),
        sa.Column("prompt_version", sa.String(length=50), nullable=False),
        sa.Column("normalization_schema_version", sa.String(length=50), nullable=False),
        sa.Column("comparison_algorithm_version", sa.String(length=50), nullable=False),
        sa.Column("consensus_algorithm_version", sa.String(length=50), nullable=False),
        sa.Column("round_one_input_hash", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("run_id", name="uq_multi_ai_consilium_run_id"),
    )
    op.create_index(
        "ix_multi_ai_consilium_runs_case_id",
        "multi_ai_consilium_runs",
        ["case_id"],
    )

    op.create_table(
        "multi_ai_consilium_participants",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("run_id", sa.Integer(), nullable=False),
        sa.Column("provider_code", sa.String(length=30), nullable=False),
        sa.Column("round_number", sa.Integer(), nullable=False),
        sa.Column("independent", sa.Boolean(), nullable=False),
        sa.Column("prompt_version", sa.String(length=50), nullable=False),
        sa.Column("input_hash", sa.String(length=64), nullable=False),
        sa.Column("model", sa.String(length=80), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        sa.Column("raw_response", sa.JSON(), nullable=True),
        sa.Column("normalized_response", sa.JSON(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("fallback_used", sa.Boolean(), nullable=False),
        sa.Column("is_mock", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["multi_ai_consilium_runs.id"], ondelete="CASCADE"),
    )
    op.create_index(
        "ix_multi_ai_consilium_participants_run_id",
        "multi_ai_consilium_participants",
        ["run_id"],
    )
    op.create_index(
        "ix_multi_ai_consilium_participants_provider_code",
        "multi_ai_consilium_participants",
        ["provider_code"],
    )


def downgrade() -> None:
    op.drop_index("ix_multi_ai_consilium_participants_provider_code", table_name="multi_ai_consilium_participants")
    op.drop_index("ix_multi_ai_consilium_participants_run_id", table_name="multi_ai_consilium_participants")
    op.drop_table("multi_ai_consilium_participants")
    op.drop_index("ix_multi_ai_consilium_runs_case_id", table_name="multi_ai_consilium_runs")
    op.drop_table("multi_ai_consilium_runs")
