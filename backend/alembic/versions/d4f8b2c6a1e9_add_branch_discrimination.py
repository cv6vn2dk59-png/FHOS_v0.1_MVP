"""add branch discrimination and information gain

Revision ID: d4f8b2c6a1e9
Revises: c3e7a9b4d2f1
"""
from alembic import op
import sqlalchemy as sa

revision = "d4f8b2c6a1e9"
down_revision = "c3e7a9b4d2f1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "branch_comparisons",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("case_id", sa.String(64), nullable=False),
        sa.Column("branch_a_uid", sa.String(128), nullable=False),
        sa.Column("branch_b_uid", sa.String(128), nullable=False),
        sa.Column("shared_fact_ids", sa.JSON(), nullable=False),
        sa.Column("differentiating_fact_ids", sa.JSON(), nullable=False),
        sa.Column("conflicting_fact_ids", sa.JSON(), nullable=False),
        sa.Column("missing_discriminator_ids", sa.JSON(), nullable=False),
        sa.Column("relationship_type", sa.String(80), nullable=False),
        sa.Column("comparison_summary", sa.Text(), nullable=False),
        sa.Column("metric_snapshot", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("case_id", "branch_a_uid", "branch_b_uid", name="uq_branch_comparison_pair"),
    )
    op.create_index("ix_branch_comparisons_case_id", "branch_comparisons", ["case_id"])

    op.create_table(
        "evidence_candidates",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("candidate_uid", sa.String(128), nullable=False, unique=True),
        sa.Column("case_id", sa.String(64), nullable=False),
        sa.Column("proposed_data_item", sa.Text(), nullable=False),
        sa.Column("evidence_type", sa.String(80), nullable=False),
        sa.Column("affected_branch_ids", sa.JSON(), nullable=False),
        sa.Column("score_inputs", sa.JSON(), nullable=False),
        sa.Column("information_gain", sa.Float(), nullable=False),
        sa.Column("priority_score", sa.Float(), nullable=False),
        sa.Column("provenance", sa.JSON(), nullable=False),
        sa.Column("limitations", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_evidence_candidates_case_id", "evidence_candidates", ["case_id"])

    op.create_table(
        "evidence_candidate_effects",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("candidate_id", sa.Integer(), sa.ForeignKey("evidence_candidates.id", ondelete="CASCADE"), nullable=False),
        sa.Column("branch_uid", sa.String(128), nullable=False),
        sa.Column("possible_result", sa.Text(), nullable=False),
        sa.Column("effect_type", sa.String(50), nullable=False),
        sa.Column("expected_strength", sa.Float(), nullable=False),
        sa.UniqueConstraint(
            "candidate_id", "branch_uid", "possible_result", "effect_type",
            name="uq_evidence_candidate_effect",
        ),
    )
    op.create_index("ix_evidence_candidate_effects_candidate_id", "evidence_candidate_effects", ["candidate_id"])


def downgrade() -> None:
    op.drop_index("ix_evidence_candidate_effects_candidate_id", table_name="evidence_candidate_effects")
    op.drop_table("evidence_candidate_effects")
    op.drop_index("ix_evidence_candidates_case_id", table_name="evidence_candidates")
    op.drop_table("evidence_candidates")
    op.drop_index("ix_branch_comparisons_case_id", table_name="branch_comparisons")
    op.drop_table("branch_comparisons")
