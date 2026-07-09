"""add contraindications table

Revision ID: a7d4f1c9b3e6
Revises: e4f6a8c1d3b5
Create Date: 2026-07-09 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a7d4f1c9b3e6'
down_revision: Union[str, Sequence[str], None] = 'e4f6a8c1d3b5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'contraindications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('substance_chebi_id', sa.String(length=50), nullable=False),
        sa.Column('disease_mondo_id', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('knowledge_source_id', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_contraindications_substance_chebi_id'), 'contraindications', ['substance_chebi_id'], unique=False)
    op.create_index(op.f('ix_contraindications_disease_mondo_id'), 'contraindications', ['disease_mondo_id'], unique=False)
    op.create_index(op.f('ix_contraindications_knowledge_source_id'), 'contraindications', ['knowledge_source_id'], unique=False)
    op.create_index('ix_contraindications_substance_disease', 'contraindications', ['substance_chebi_id', 'disease_mondo_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_contraindications_substance_disease', table_name='contraindications')
    op.drop_index(op.f('ix_contraindications_knowledge_source_id'), table_name='contraindications')
    op.drop_index(op.f('ix_contraindications_disease_mondo_id'), table_name='contraindications')
    op.drop_index(op.f('ix_contraindications_substance_chebi_id'), table_name='contraindications')
    op.drop_table('contraindications')
