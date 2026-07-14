"""add biomechanical load adaptation and overload

Revision ID: j0f4h8c2g7e9
Revises: i9e3g7b1f6d8
"""
from alembic import op
import sqlalchemy as sa
revision = "j0f4h8c2g7e9"
down_revision = "i9e3g7b1f6d8"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table("biomechanical_load_exposures",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("exposure_uid", sa.String(160), nullable=False, unique=True),
        sa.Column("case_id", sa.String(64), nullable=False), sa.Column("exposure_kind", sa.String(50), nullable=False),
        sa.Column("code", sa.String(120), nullable=False), sa.Column("exposure_snapshot", sa.JSON(), nullable=False),
        sa.Column("provenance", sa.JSON(), nullable=False), sa.Column("context_constraints", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_biomechanical_load_exposures_case_id", "biomechanical_load_exposures", ["case_id"])
    op.create_index("ix_biomechanical_load_exposures_code", "biomechanical_load_exposures", ["code"])
    op.create_table("biomechanical_load_assessments",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("case_id", sa.String(64), nullable=False, unique=True),
        sa.Column("mismatch_snapshot", sa.JSON(), nullable=False), sa.Column("effect_snapshot", sa.JSON(), nullable=False),
        sa.Column("branch_assessment_snapshot", sa.JSON(), nullable=False), sa.Column("missing_evidence_snapshot", sa.JSON(), nullable=False),
        sa.Column("limitations", sa.JSON(), nullable=False), sa.Column("prohibited_conclusions", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))

def downgrade() -> None:
    op.drop_table("biomechanical_load_assessments")
    op.drop_index("ix_biomechanical_load_exposures_code", table_name="biomechanical_load_exposures")
    op.drop_index("ix_biomechanical_load_exposures_case_id", table_name="biomechanical_load_exposures")
    op.drop_table("biomechanical_load_exposures")
