"""add clinical causality layer

Revision ID: f8b3d6a2c1e4
Revises: a9d4e7c2b6f1
"""
from alembic import op
import sqlalchemy as sa

revision = "f8b3d6a2c1e4"
down_revision = "a9d4e7c2b6f1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("causal_graph_nodes",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("case_id", sa.String(64), nullable=False),
        sa.Column("external_node_id", sa.String(255), nullable=False), sa.Column("node_kind", sa.String(50), nullable=False),
        sa.Column("label", sa.String(255), nullable=False), sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("case_id", "external_node_id", name="uq_causal_node_case_external"))
    op.create_index("ix_causal_graph_nodes_case_id", "causal_graph_nodes", ["case_id"])
    op.create_table("causal_graph_edges",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("case_id", sa.String(64), nullable=False),
        sa.Column("source_node_id", sa.String(255), nullable=False), sa.Column("target_node_id", sa.String(255), nullable=False),
        sa.Column("relation_type", sa.String(80), nullable=False), sa.Column("evidence_strength", sa.String(40), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False), sa.Column("provenance", sa.JSON(), nullable=False),
        sa.Column("context_constraints", sa.JSON(), nullable=False))
    op.create_index("ix_causal_graph_edges_case_id", "causal_graph_edges", ["case_id"])


def downgrade() -> None:
    op.drop_index("ix_causal_graph_edges_case_id", table_name="causal_graph_edges")
    op.drop_table("causal_graph_edges")
    op.drop_index("ix_causal_graph_nodes_case_id", table_name="causal_graph_nodes")
    op.drop_table("causal_graph_nodes")

