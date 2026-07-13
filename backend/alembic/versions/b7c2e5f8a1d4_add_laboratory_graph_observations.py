"""add laboratory graph observations

Revision ID: b7c2e5f8a1d4
Revises: d1a4e7c9b2f0
"""
from alembic import op
import sqlalchemy as sa

revision = "b7c2e5f8a1d4"
down_revision = "d1a4e7c9b2f0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "laboratory_graph_observations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("laboratory_result_id", sa.Integer(), nullable=False),
        sa.Column("patient_node_state_id", sa.Integer(), nullable=False),
        sa.Column("patient_id", sa.String(length=64), nullable=False),
        sa.Column("episode_id", sa.String(length=64), nullable=False),
        sa.Column("node_id", sa.String(length=255), nullable=False),
        sa.Column("test_code", sa.String(length=100), nullable=False),
        sa.Column("value", sa.Float(), nullable=True),
        sa.Column("unit", sa.String(length=50), nullable=True),
        sa.Column("reference_min", sa.Float(), nullable=True),
        sa.Column("reference_max", sa.Float(), nullable=True),
        sa.Column("critical_low", sa.Float(), nullable=True),
        sa.Column("critical_high", sa.Float(), nullable=True),
        sa.Column("interpretation", sa.String(length=30), nullable=False),
        sa.Column("observation_class", sa.String(length=30), nullable=False),
        sa.Column("evidence_role", sa.String(length=20), nullable=False),
        sa.Column("result_date", sa.Date(), nullable=True),
        sa.Column("provenance", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["laboratory_result_id"], ["laboratory_results.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["patient_node_state_id"], ["patient_node_states.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["node_id"], ["health_nodes.external_id"], ondelete="CASCADE"),
        sa.UniqueConstraint("laboratory_result_id"),
    )
    op.create_index("ix_laboratory_graph_observations_patient_id", "laboratory_graph_observations", ["patient_id"])
    op.create_index("ix_laboratory_graph_observations_episode_id", "laboratory_graph_observations", ["episode_id"])
    op.create_index(
        "ix_lab_graph_observation_patient_episode",
        "laboratory_graph_observations",
        ["patient_id", "episode_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_lab_graph_observation_patient_episode", table_name="laboratory_graph_observations")
    op.drop_index("ix_laboratory_graph_observations_episode_id", table_name="laboratory_graph_observations")
    op.drop_index("ix_laboratory_graph_observations_patient_id", table_name="laboratory_graph_observations")
    op.drop_table("laboratory_graph_observations")
