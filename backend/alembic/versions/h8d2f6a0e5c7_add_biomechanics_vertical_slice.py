"""add biomechanics vertical slice

Revision ID: h8d2f6a0e5c7
Revises: g7c1e5f9d4b6
"""
from alembic import op
import sqlalchemy as sa

revision = "h8d2f6a0e5c7"
down_revision = "g7c1e5f9d4b6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "biomechanical_facts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("fact_uid", sa.String(160), nullable=False, unique=True),
        sa.Column("case_id", sa.String(64), nullable=False),
        sa.Column("fact_kind", sa.String(50), nullable=False),
        sa.Column("code", sa.String(100), nullable=False),
        sa.Column("value_json", sa.JSON(), nullable=False),
        sa.Column("laterality", sa.String(20), nullable=True),
        sa.Column("body_region", sa.String(100), nullable=True),
        sa.Column("provenance", sa.JSON(), nullable=False),
        sa.Column("context_constraints", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_biomechanical_facts_case_id", "biomechanical_facts", ["case_id"])
    op.create_index("ix_biomechanical_facts_code", "biomechanical_facts", ["code"])
    op.create_table(
        "biomechanics_expansions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("case_id", sa.String(64), nullable=False, unique=True),
        sa.Column("branch_ids", sa.JSON(), nullable=False),
        sa.Column("relationship_ids", sa.JSON(), nullable=False),
        sa.Column("unassigned_fact_ids", sa.JSON(), nullable=False),
        sa.Column("red_flag_branch_ids", sa.JSON(), nullable=False),
        sa.Column("missing_evidence_ids", sa.JSON(), nullable=False),
        sa.Column("limitations", sa.JSON(), nullable=False),
        sa.Column("prohibited_conclusions", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("biomechanics_expansions")
    op.drop_index("ix_biomechanical_facts_code", table_name="biomechanical_facts")
    op.drop_index("ix_biomechanical_facts_case_id", table_name="biomechanical_facts")
    op.drop_table("biomechanical_facts")
