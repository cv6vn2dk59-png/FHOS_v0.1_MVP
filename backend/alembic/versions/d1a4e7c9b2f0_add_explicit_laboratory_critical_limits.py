"""add explicit laboratory critical limits

Revision ID: d1a4e7c9b2f0
Revises: c8e1f4a9b2d7
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "d1a4e7c9b2f0"
down_revision: Union[str, Sequence[str], None] = "c8e1f4a9b2d7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("laboratory_results", sa.Column("critical_low", sa.Float(), nullable=True))
    op.add_column("laboratory_results", sa.Column("critical_high", sa.Float(), nullable=True))

    # Existing critical interpretations were generated from a percentage
    # deviation heuristic, not from verified analyte-specific critical limits.
    # Normalize them to directional out-of-range statuses.
    op.execute(
        "UPDATE laboratory_results "
        "SET interpretation = 'low' "
        "WHERE interpretation = 'critical_low'"
    )
    op.execute(
        "UPDATE laboratory_results "
        "SET interpretation = 'high' "
        "WHERE interpretation = 'critical_high'"
    )


def downgrade() -> None:
    op.drop_column("laboratory_results", "critical_high")
    op.drop_column("laboratory_results", "critical_low")
