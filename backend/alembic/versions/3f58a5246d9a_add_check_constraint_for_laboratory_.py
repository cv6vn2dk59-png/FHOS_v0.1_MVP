"""add check constraint for laboratory interpretation

Revision ID: 3f58a5246d9a
Revises: f5ecf766c94f
Create Date: 2026-07-02 23:42:16.902500

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3f58a5246d9a'
down_revision: Union[str, Sequence[str], None] = 'f5ecf766c94f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("laboratory_results") as batch_op:
        batch_op.create_check_constraint(
            "ck_laboratory_results_interpretation_valid",
            "interpretation IN ('normal', 'low', 'high', 'critical_low', 'critical_high', 'unknown')",
        )

def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("laboratory_results") as batch_op:
        batch_op.drop_constraint(
            "ck_laboratory_results_interpretation_valid",
            type_="check",
        )