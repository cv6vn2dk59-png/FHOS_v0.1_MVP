"""add diseases table

Revision ID: e4f6a8c1d3b5
Revises: 9a3d7c1f2b6e
Create Date: 2026-07-08 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e4f6a8c1d3b5'
down_revision: Union[str, Sequence[str], None] = '9a3d7c1f2b6e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'diseases',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('patient_profile_id', sa.Integer(), nullable=True),
        sa.Column('diagnosis_name', sa.String(length=255), nullable=False),
        sa.Column('icd_code', sa.String(length=20), nullable=True),
        sa.Column('onset_date', sa.Date(), nullable=False),
        sa.Column('resolved_date', sa.Date(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint('resolved_date IS NULL OR resolved_date >= onset_date', name='ck_diseases_resolved_after_onset'),
        sa.ForeignKeyConstraint(['patient_profile_id'], ['patient_profiles.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_diseases_icd_code'), 'diseases', ['icd_code'], unique=False)
    op.create_index(op.f('ix_diseases_diagnosis_name'), 'diseases', ['diagnosis_name'], unique=False)
    op.create_index('ix_diseases_patient_diagnosis_onset', 'diseases', ['patient_profile_id', 'diagnosis_name', 'onset_date'], unique=False)
    op.create_index(op.f('ix_diseases_patient_profile_id'), 'diseases', ['patient_profile_id'], unique=False)
    op.create_index(op.f('ix_diseases_onset_date'), 'diseases', ['onset_date'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_diseases_onset_date'), table_name='diseases')
    op.drop_index(op.f('ix_diseases_patient_profile_id'), table_name='diseases')
    op.drop_index('ix_diseases_patient_diagnosis_onset', table_name='diseases')
    op.drop_index(op.f('ix_diseases_diagnosis_name'), table_name='diseases')
    op.drop_index(op.f('ix_diseases_icd_code'), table_name='diseases')
    op.drop_table('diseases')
