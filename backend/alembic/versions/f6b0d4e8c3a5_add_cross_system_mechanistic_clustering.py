"""add cross system mechanistic clustering

Revision ID: f6b0d4e8c3a5
Revises: e5a9c3d7b2f4
"""
from alembic import op
import sqlalchemy as sa

revision = "f6b0d4e8c3a5"
down_revision = "e5a9c3d7b2f4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "mechanistic_clusters_v2",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("cluster_uid", sa.String(180), nullable=False, unique=True),
        sa.Column("case_id", sa.String(64), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("cluster_type", sa.String(80), nullable=False),
        sa.Column("branch_ids", sa.JSON(), nullable=False),
        sa.Column("body_systems", sa.JSON(), nullable=False),
        sa.Column("shared_item_ids", sa.JSON(), nullable=False),
        sa.Column("evidence_strength", sa.String(40), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("provenance", sa.JSON(), nullable=False),
        sa.Column("context_constraints", sa.JSON(), nullable=False),
        sa.Column("member_branches_preserved", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_mechanistic_clusters_v2_case_id", "mechanistic_clusters_v2", ["case_id"])
    op.create_table(
        "mechanistic_cluster_conflicts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("case_id", sa.String(64), nullable=False),
        sa.Column("cluster_uid", sa.String(180), nullable=True),
        sa.Column("conflict_code", sa.String(100), nullable=False),
        sa.Column("branch_ids", sa.JSON(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_mechanistic_cluster_conflicts_case_id", "mechanistic_cluster_conflicts", ["case_id"])


def downgrade() -> None:
    op.drop_index("ix_mechanistic_cluster_conflicts_case_id", table_name="mechanistic_cluster_conflicts")
    op.drop_table("mechanistic_cluster_conflicts")
    op.drop_index("ix_mechanistic_clusters_v2_case_id", table_name="mechanistic_clusters_v2")
    op.drop_table("mechanistic_clusters_v2")
