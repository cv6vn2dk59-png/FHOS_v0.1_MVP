"""add icd11 nodes table

Revision ID: f2b8d5a1c7e3
Revises: a7d4f1c9b3e6
Create Date: 2026-07-09 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f2b8d5a1c7e3'
down_revision: Union[str, Sequence[str], None] = 'a7d4f1c9b3e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'icd11_nodes',
        sa.Column('id', sa.String(length=500), nullable=False),
        sa.Column('parent_id', sa.String(length=500), nullable=True),
        sa.Column('icd_code', sa.String(length=20), nullable=True),
        sa.Column('english_title', sa.Text(), nullable=False),
        sa.Column('ukrainian_title', sa.Text(), nullable=True),
        sa.Column('translation_status', sa.Enum('VERIFIED', 'AUTO_IMPORTED', 'NEEDS_REVIEW', 'MISSING', name='icd11_translation_status'), nullable=False),
        sa.Column('node_kind', sa.Enum('CHAPTER', 'BLOCK', 'CATEGORY', name='icd11_node_kind'), nullable=False),
        sa.Column('special_code', sa.Enum('NONE', 'Y', 'Z', name='icd11_special_code'), nullable=False),
        sa.Column('sort_order', sa.Integer(), nullable=False),
        sa.Column('source_release', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['parent_id'], ['icd11_nodes.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_icd11_nodes_parent_id'), 'icd11_nodes', ['parent_id'], unique=False)
    op.create_index(op.f('ix_icd11_nodes_icd_code'), 'icd11_nodes', ['icd_code'], unique=False)
    op.create_index(op.f('ix_icd11_nodes_node_kind'), 'icd11_nodes', ['node_kind'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_icd11_nodes_node_kind'), table_name='icd11_nodes')
    op.drop_index(op.f('ix_icd11_nodes_icd_code'), table_name='icd11_nodes')
    op.drop_index(op.f('ix_icd11_nodes_parent_id'), table_name='icd11_nodes')
    op.drop_table('icd11_nodes')
