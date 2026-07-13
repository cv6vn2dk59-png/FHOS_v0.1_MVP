"""add biomechanical examination and functional provocation

Revision ID: i9e3g7b1f6d8
Revises: h8d2f6a0e5c7
"""
from alembic import op
import sqlalchemy as sa

revision = "i9e3g7b1f6d8"
down_revision = "h8d2f6a0e5c7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "biomechanical_examination_findings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("finding_uid", sa.String(160), nullable=False, unique=True),
        sa.Column("case_id", sa.String(64), nullable=False),
        sa.Column("finding_kind", sa.String(60), nullable=False),
        sa.Column("code", sa.String(120), nullable=False),
        sa.Column("result", sa.String(30), nullable=False),
        sa.Column("value_json", sa.JSON(), nullable=False),
        sa.Column("body_region", sa.String(100), nullable=True),
        sa.Column("laterality", sa.String(20), nullable=True),
        sa.Column("provenance", sa.JSON(), nullable=False),
        sa.Column("context_constraints", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_biomechanical_examination_findings_case_id", "biomechanical_examination_findings", ["case_id"])
    op.create_index("ix_biomechanical_examination_findings_code", "biomechanical_examination_findings", ["code"])
    op.create_table(
        "biomechanical_examination_assessments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("case_id", sa.String(64), nullable=False, unique=True),
        sa.Column("effect_snapshot", sa.JSON(), nullable=False),
        sa.Column("branch_assessment_snapshot", sa.JSON(), nullable=False),
        sa.Column("missing_evidence_snapshot", sa.JSON(), nullable=False),
        sa.Column("safety_escalation_branch_ids", sa.JSON(), nullable=False),
        sa.Column("unassigned_finding_ids", sa.JSON(), nullable=False),
        sa.Column("limitations", sa.JSON(), nullable=False),
        sa.Column("prohibited_conclusions", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("biomechanical_examination_assessments")
    op.drop_index("ix_biomechanical_examination_findings_code", table_name="biomechanical_examination_findings")
    op.drop_index("ix_biomechanical_examination_findings_case_id", table_name="biomechanical_examination_findings")
    op.drop_table("biomechanical_examination_findings")
