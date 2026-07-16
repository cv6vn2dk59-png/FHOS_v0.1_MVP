"""add rule passport (FHOS-RULE-R-11) and branch closure clinician confirmation (FHOS-RULE-R-14)

Revision ID: k1b5f9a3d7c2
Revises: j0f4h8c2g7e9
"""
from alembic import op
import sqlalchemy as sa
revision = "k1b5f9a3d7c2"
down_revision = "j0f4h8c2g7e9"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table("rule_passports",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("rule_id", sa.String(100), nullable=False),
        sa.Column("version", sa.String(20), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("source_type", sa.String(50), nullable=False),
        sa.Column("evidence_strength", sa.String(40), nullable=False),
        sa.Column("limitations", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("rule_id", "version", name="uq_rule_passport_id_version"),
    )
    op.create_index("ix_rule_passports_rule_id", "rule_passports", ["rule_id"])

    op.add_column(
        "hypothesis_branches",
        sa.Column("clinician_confirmed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )

def downgrade() -> None:
    op.drop_column("hypothesis_branches", "clinician_confirmed")
    op.drop_index("ix_rule_passports_rule_id", table_name="rule_passports")
    op.drop_table("rule_passports")
