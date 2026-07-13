"""add temporal causality and clinical timeline

Revision ID: e5a9c3d7b2f4
Revises: d4f8b2c6a1e9
"""
from alembic import op
import sqlalchemy as sa

revision = "e5a9c3d7b2f4"
down_revision = "d4f8b2c6a1e9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "clinical_timeline_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_uid", sa.String(128), nullable=False, unique=True),
        sa.Column("case_id", sa.String(64), nullable=False),
        sa.Column("event_kind", sa.String(50), nullable=False),
        sa.Column("label", sa.String(255), nullable=False),
        sa.Column("temporal_interval", sa.JSON(), nullable=False),
        sa.Column("precision", sa.String(30), nullable=False),
        sa.Column("branch_ids", sa.JSON(), nullable=False),
        sa.Column("provenance", sa.JSON(), nullable=False),
        sa.Column("context", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_clinical_timeline_events_case_id", "clinical_timeline_events", ["case_id"])
    op.create_table(
        "temporal_relations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("case_id", sa.String(64), nullable=False),
        sa.Column("source_event_uid", sa.String(128), nullable=False),
        sa.Column("target_event_uid", sa.String(128), nullable=False),
        sa.Column("relation_kind", sa.String(40), nullable=False),
        sa.Column("certainty", sa.Float(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("case_id", "source_event_uid", "target_event_uid", name="uq_temporal_relation_pair"),
    )
    op.create_index("ix_temporal_relations_case_id", "temporal_relations", ["case_id"])
    op.create_table(
        "temporal_conflicts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("conflict_uid", sa.String(160), nullable=False, unique=True),
        sa.Column("case_id", sa.String(64), nullable=False),
        sa.Column("link_uid", sa.String(128), nullable=False),
        sa.Column("conflict_type", sa.String(60), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("source_event_uid", sa.String(128), nullable=False),
        sa.Column("target_event_uid", sa.String(128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_temporal_conflicts_case_id", "temporal_conflicts", ["case_id"])
    op.create_table(
        "missing_temporal_evidence",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("missing_uid", sa.String(160), nullable=False, unique=True),
        sa.Column("case_id", sa.String(64), nullable=False),
        sa.Column("event_ids", sa.JSON(), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("priority", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_missing_temporal_evidence_case_id", "missing_temporal_evidence", ["case_id"])


def downgrade() -> None:
    op.drop_index("ix_missing_temporal_evidence_case_id", table_name="missing_temporal_evidence")
    op.drop_table("missing_temporal_evidence")
    op.drop_index("ix_temporal_conflicts_case_id", table_name="temporal_conflicts")
    op.drop_table("temporal_conflicts")
    op.drop_index("ix_temporal_relations_case_id", table_name="temporal_relations")
    op.drop_table("temporal_relations")
    op.drop_index("ix_clinical_timeline_events_case_id", table_name="clinical_timeline_events")
    op.drop_table("clinical_timeline_events")
