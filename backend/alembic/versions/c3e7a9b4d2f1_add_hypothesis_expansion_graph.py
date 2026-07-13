"""add hypothesis expansion graph

Revision ID: c3e7a9b4d2f1
Revises: f8b3d6a2c1e4
"""
from alembic import op
import sqlalchemy as sa

revision = "c3e7a9b4d2f1"
down_revision = "f8b3d6a2c1e4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("hypothesis_branches",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("branch_uid", sa.String(128), nullable=False, unique=True),
        sa.Column("case_id", sa.String(64), nullable=False), sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False), sa.Column("causal_domain", sa.String(100), nullable=False),
        sa.Column("branch_type", sa.String(80), nullable=False), sa.Column("status", sa.String(40), nullable=False),
        sa.Column("root_trigger_ids", sa.JSON(), nullable=False), sa.Column("node_ids", sa.JSON(), nullable=False),
        sa.Column("edge_ids", sa.JSON(), nullable=False), sa.Column("supporting_fact_ids", sa.JSON(), nullable=False),
        sa.Column("contradicting_fact_ids", sa.JSON(), nullable=False), sa.Column("neutral_fact_ids", sa.JSON(), nullable=False),
        sa.Column("missing_evidence_ids", sa.JSON(), nullable=False), sa.Column("evidence_strength", sa.String(40), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False), sa.Column("provenance", sa.JSON(), nullable=False),
        sa.Column("context_constraints", sa.JSON(), nullable=False), sa.Column("safety_critical", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_hypothesis_branches_case_id", "hypothesis_branches", ["case_id"])
    op.create_table("branch_relationships",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("relationship_uid", sa.String(255), nullable=False, unique=True),
        sa.Column("case_id", sa.String(64), nullable=False), sa.Column("source_branch_uid", sa.String(128), nullable=False),
        sa.Column("target_branch_uid", sa.String(128), nullable=False), sa.Column("relationship_type", sa.String(80), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False), sa.Column("evidence_strength", sa.String(40), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False), sa.Column("provenance", sa.JSON(), nullable=False),
        sa.Column("context_constraints", sa.JSON(), nullable=False))
    op.create_index("ix_branch_relationships_case_id", "branch_relationships", ["case_id"])


def downgrade() -> None:
    op.drop_index("ix_branch_relationships_case_id", table_name="branch_relationships")
    op.drop_table("branch_relationships")
    op.drop_index("ix_hypothesis_branches_case_id", table_name="hypothesis_branches")
    op.drop_table("hypothesis_branches")
