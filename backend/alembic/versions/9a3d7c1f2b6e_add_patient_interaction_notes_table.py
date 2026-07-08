"""add patient_interaction_notes table

Revision ID: 9a3d7c1f2b6e
Revises: 4866a7e4c6ea
Create Date: 2026-07-08 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9a3d7c1f2b6e'
down_revision: Union[str, Sequence[str], None] = '4866a7e4c6ea'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'patient_interaction_notes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('patient_profile_id', sa.Integer(), nullable=True),
        sa.Column('substance_a', sa.String(length=255), nullable=False),
        sa.Column('substance_b', sa.String(length=255), nullable=False),
        sa.Column('note_text', sa.String(length=2000), nullable=False),
        sa.Column('unverified', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['patient_profile_id'], ['patient_profiles.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_patient_interaction_notes_patient_profile_id'),
        'patient_interaction_notes', ['patient_profile_id'], unique=False,
    )
    op.create_index(
        'ix_patient_interaction_notes_patient_pair',
        'patient_interaction_notes', ['patient_profile_id', 'substance_a', 'substance_b'], unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_patient_interaction_notes_patient_pair', table_name='patient_interaction_notes')
    op.drop_index(
        op.f('ix_patient_interaction_notes_patient_profile_id'),
        table_name='patient_interaction_notes',
    )
    op.drop_table('patient_interaction_notes')
