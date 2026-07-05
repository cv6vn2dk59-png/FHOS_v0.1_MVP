"""make reference_range bounds nullable, support one sided ranges

Revision ID: 1dde201b18a4
Revises: 798c1de9ceb1
Create Date: 2026-07-05 12:36:15.103584

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1dde201b18a4'
down_revision: Union[str, Sequence[str], None] = '798c1de9ceb1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("reference_ranges") as batch_op:
        batch_op.alter_column("reference_min", existing_type=sa.Float(), nullable=True)
        batch_op.alter_column("reference_max", existing_type=sa.Float(), nullable=True)
        batch_op.drop_constraint("ck_reference_ranges_min_max", type_="check")
        batch_op.create_check_constraint(
            "ck_reference_ranges_min_max_valid",
            "(reference_min IS NOT NULL OR reference_max IS NOT NULL) "
            "AND (reference_min IS NULL OR reference_max IS NULL OR reference_min <= reference_max)",
        )


def downgrade() -> None:
    with op.batch_alter_table("reference_ranges") as batch_op:
        batch_op.drop_constraint("ck_reference_ranges_min_max_valid", type_="check")
        batch_op.create_check_constraint("ck_reference_ranges_min_max", "reference_min <= reference_max")
        batch_op.alter_column("reference_max", existing_type=sa.Float(), nullable=False)
        batch_op.alter_column("reference_min", existing_type=sa.Float(), nullable=False)
