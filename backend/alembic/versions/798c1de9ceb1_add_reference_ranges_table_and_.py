"""add reference_ranges table and reference_range_status column

Revision ID: 798c1de9ceb1
Revises: 3f58a5246d9a
Create Date: 2026-07-04 06:20:55.297175

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '798c1de9ceb1'
down_revision: Union[str, Sequence[str], None] = '3f58a5246d9a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('reference_ranges',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('test_code', sa.String(length=100), nullable=False),
    sa.Column('test_name', sa.String(length=255), nullable=False),
    sa.Column('unit', sa.String(length=50), nullable=False),
    sa.Column('sex', sa.String(length=20), nullable=True),
    sa.Column('age_min', sa.Integer(), nullable=True),
    sa.Column('age_max', sa.Integer(), nullable=True),
    sa.Column('reference_min', sa.Float(), nullable=False),
    sa.Column('reference_max', sa.Float(), nullable=False),
    sa.Column('source', sa.String(length=255), nullable=True),
    sa.Column('laboratory_name', sa.String(length=255), nullable=True),
    sa.Column('method', sa.String(length=100), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.CheckConstraint('reference_min <= reference_max', name='ck_reference_ranges_min_max'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_reference_ranges_test_code'), 'reference_ranges', ['test_code'], unique=False)
    op.create_index('ix_reference_ranges_test_code_unit', 'reference_ranges', ['test_code', 'unit'], unique=False)

    # sa.Enum усередині add_column (на відміну від create_table) НЕ створює
    # тип автоматично на PostgreSQL - потрібно явно. На SQLite create()
    # тут безпечний no-op (там немає окремого CREATE TYPE), тому підхід
    # крос-діалектний.
    reference_range_status_type = sa.Enum(
        'manual', 'resolved', 'not_found',
        name='reference_range_status',
    )
    reference_range_status_type.create(op.get_bind(), checkfirst=True)

    op.add_column(
        'laboratory_results',
        sa.Column('reference_range_status', reference_range_status_type, nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('laboratory_results', 'reference_range_status')

    sa.Enum(name='reference_range_status').drop(op.get_bind(), checkfirst=True)

    op.drop_index('ix_reference_ranges_test_code_unit', table_name='reference_ranges')
    op.drop_index(op.f('ix_reference_ranges_test_code'), table_name='reference_ranges')
    op.drop_table('reference_ranges')