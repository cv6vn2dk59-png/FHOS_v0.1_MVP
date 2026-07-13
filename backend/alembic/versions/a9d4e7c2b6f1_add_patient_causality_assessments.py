"""add patient causality assessments

Revision ID: a9d4e7c2b6f1
Revises: e6a1c9d4b7f2
Create Date: 2026-07-13
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "a9d4e7c2b6f1"
down_revision: Union[str, None] = "e6a1c9d4b7f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "patient_causality_assessments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("patient_id", sa.String(length=64), nullable=False),
        sa.Column("episode_id", sa.String(length=64), nullable=False),
        sa.Column("input_result_ids", sa.JSON(), nullable=False),
        sa.Column("assessment_snapshot", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("patient_id", "episode_id", name="uq_patient_causality_assessment_episode"),
    )
    op.create_index(
        "ix_patient_causality_assessment_lookup",
        "patient_causality_assessments",
        ["patient_id", "episode_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_patient_causality_assessment_lookup", table_name="patient_causality_assessments")
    op.drop_table("patient_causality_assessments")

