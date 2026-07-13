"""add evidence model and structured consilium

Revision ID: e6a1c9d4b7f2
Revises: b7c2e5f8a1d4
Create Date: 2026-07-13
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "e6a1c9d4b7f2"
down_revision: Union[str, None] = "b7c2e5f8a1d4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "evidence_sources",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source_key", sa.String(length=255), nullable=False),
        sa.Column("source_type", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("uri", sa.Text(), nullable=True),
        sa.Column("publication_type", sa.String(length=100), nullable=True),
        sa.Column("verification_status", sa.String(length=40), nullable=False),
        sa.Column("evidence_strength", sa.String(length=40), nullable=False),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source_key"),
    )
    op.create_table(
        "hypothesis_evidence",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("hypothesis_key", sa.String(length=255), nullable=False),
        sa.Column("evidence_source_id", sa.Integer(), nullable=True),
        sa.Column("patient_fact_id", sa.String(length=255), nullable=True),
        sa.Column("role", sa.String(length=30), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["evidence_source_id"], ["evidence_sources.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("hypothesis_key", "evidence_source_id", "patient_fact_id", "role", name="uq_hypothesis_evidence_assignment"),
    )
    op.create_index(op.f("ix_hypothesis_evidence_hypothesis_key"), "hypothesis_evidence", ["hypothesis_key"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_hypothesis_evidence_hypothesis_key"), table_name="hypothesis_evidence")
    op.drop_table("hypothesis_evidence")
    op.drop_table("evidence_sources")
