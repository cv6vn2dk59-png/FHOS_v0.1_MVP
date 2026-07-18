"""add real provider runtime fields

Revision ID: n5e9c2a7d4f1
Revises: m4d8a2c6f1e3
"""

from alembic import op
import sqlalchemy as sa


revision = "n5e9c2a7d4f1"
down_revision = "m4d8a2c6f1e3"
branch_labels = None
depends_on = None


def _column_names(table_name: str) -> set[str]:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return {column["name"] for column in inspector.get_columns(table_name)}


def upgrade() -> None:
    run_columns = _column_names("multi_ai_consilium_runs")
    participant_columns = _column_names("multi_ai_consilium_participants")

    if "system_prompt_version" not in run_columns:
        op.add_column(
            "multi_ai_consilium_runs",
            sa.Column("system_prompt_version", sa.String(length=50), nullable=False, server_default="multi-ai-system.v1"),
        )
    if "round_one_prompt_version" not in run_columns:
        op.add_column(
            "multi_ai_consilium_runs",
            sa.Column("round_one_prompt_version", sa.String(length=50), nullable=False, server_default="multi-ai-round-one.v1"),
        )
    if "round_two_prompt_version" not in run_columns:
        op.add_column(
            "multi_ai_consilium_runs",
            sa.Column("round_two_prompt_version", sa.String(length=50), nullable=False, server_default="multi-ai-round-two.v1"),
        )
    if "devil_prompt_version" not in run_columns:
        op.add_column(
            "multi_ai_consilium_runs",
            sa.Column("devil_prompt_version", sa.String(length=50), nullable=False, server_default="multi-ai-devil.v1"),
        )
    if "case_package_hash" not in run_columns:
        op.add_column(
            "multi_ai_consilium_runs",
            sa.Column("case_package_hash", sa.String(length=64), nullable=False, server_default=""),
        )

    if "provider_model" not in participant_columns:
        op.add_column(
            "multi_ai_consilium_participants",
            sa.Column("provider_model", sa.String(length=120), nullable=False, server_default="placeholder"),
        )
    if "execution_mode" not in participant_columns:
        op.add_column(
            "multi_ai_consilium_participants",
            sa.Column("execution_mode", sa.String(length=20), nullable=False, server_default="mock"),
        )
    if "prompt_hash" not in participant_columns:
        op.add_column(
            "multi_ai_consilium_participants",
            sa.Column("prompt_hash", sa.String(length=64), nullable=False, server_default=""),
        )
    if "error_code" not in participant_columns:
        op.add_column(
            "multi_ai_consilium_participants",
            sa.Column("error_code", sa.String(length=80), nullable=True),
        )
    if "error_message" not in participant_columns:
        op.add_column(
            "multi_ai_consilium_participants",
            sa.Column("error_message", sa.Text(), nullable=True),
        )
    if "real_provider_call" not in participant_columns:
        op.add_column(
            "multi_ai_consilium_participants",
            sa.Column("real_provider_call", sa.Boolean(), nullable=False, server_default=sa.false()),
        )
    if "attempt_count" not in participant_columns:
        op.add_column(
            "multi_ai_consilium_participants",
            sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        )
    if "usage" not in participant_columns:
        op.add_column(
            "multi_ai_consilium_participants",
            sa.Column("usage", sa.JSON(), nullable=True),
        )


def downgrade() -> None:
    op.drop_column("multi_ai_consilium_participants", "usage")
    op.drop_column("multi_ai_consilium_participants", "attempt_count")
    op.drop_column("multi_ai_consilium_participants", "real_provider_call")
    op.drop_column("multi_ai_consilium_participants", "error_message")
    op.drop_column("multi_ai_consilium_participants", "error_code")
    op.drop_column("multi_ai_consilium_participants", "prompt_hash")
    op.drop_column("multi_ai_consilium_participants", "execution_mode")
    op.drop_column("multi_ai_consilium_participants", "provider_model")

    op.drop_column("multi_ai_consilium_runs", "case_package_hash")
    op.drop_column("multi_ai_consilium_runs", "devil_prompt_version")
    op.drop_column("multi_ai_consilium_runs", "round_two_prompt_version")
    op.drop_column("multi_ai_consilium_runs", "round_one_prompt_version")
    op.drop_column("multi_ai_consilium_runs", "system_prompt_version")
