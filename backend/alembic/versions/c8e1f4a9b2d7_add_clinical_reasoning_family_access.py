"""add clinical reasoning graph persistence and family access

Revision ID: c8e1f4a9b2d7
Revises: f2b8d5a1c7e3
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "c8e1f4a9b2d7"
down_revision: Union[str, Sequence[str], None] = "f2b8d5a1c7e3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("health_nodes", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("external_id", sa.String(255), nullable=False, unique=True), sa.Column("external_source", sa.String(50), nullable=False), sa.Column("label", sa.String(255), nullable=False), sa.Column("node_kind", sa.String(50), nullable=False))
    op.create_table("health_relations", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("from_node_id", sa.String(255), sa.ForeignKey("health_nodes.external_id", ondelete="CASCADE"), nullable=False), sa.Column("to_node_id", sa.String(255), sa.ForeignKey("health_nodes.external_id", ondelete="CASCADE"), nullable=False), sa.Column("relation_kind", sa.String(50), nullable=False), sa.Column("evidence_level", sa.String(50), nullable=False), sa.Column("source_citation", sa.Text(), nullable=False), sa.Column("is_directed", sa.Boolean(), nullable=False, server_default=sa.true()), sa.UniqueConstraint("from_node_id", "to_node_id", "relation_kind", "source_citation", name="uq_health_relation_evidence"))
    op.create_table("clinical_hypotheses", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("symptom_node_id", sa.String(255), sa.ForeignKey("health_nodes.external_id", ondelete="CASCADE"), nullable=False), sa.Column("title", sa.String(255), nullable=False), sa.Column("mechanism", sa.Text(), nullable=False), sa.Column("origin", sa.String(30), nullable=False), sa.Column("evidence_level", sa.String(50), nullable=False), sa.Column("anatomical_source", sa.String(255)), sa.Column("body_system", sa.String(100)), sa.Column("etiology_category", sa.String(100)), sa.Column("verification_questions", sa.JSON(), nullable=False), sa.Column("supporting_evidence", sa.JSON(), nullable=False), sa.Column("contradicting_evidence", sa.JSON(), nullable=False), sa.Column("missing_evidence", sa.JSON(), nullable=False), sa.Column("source_ids", sa.JSON(), nullable=False), sa.Column("status", sa.String(40), nullable=False, server_default="candidate_hypotheses"), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_table("patient_node_states", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("patient_id", sa.String(64), nullable=False), sa.Column("node_id", sa.String(255), sa.ForeignKey("health_nodes.external_id", ondelete="CASCADE"), nullable=False), sa.Column("episode_id", sa.String(64), nullable=False), sa.Column("activated_at", sa.DateTime(timezone=True), nullable=False), sa.Column("family_link_reason", sa.String(100)), sa.UniqueConstraint("patient_id", "node_id", "episode_id", name="uq_patient_node_episode"))
    op.create_table("family_data_consents", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("subject_patient_id", sa.String(64), nullable=False), sa.Column("granted_to_actor_id", sa.String(64), nullable=False), sa.Column("purpose_code", sa.String(100), nullable=False), sa.Column("resource_node_ids", sa.JSON(), nullable=False), sa.Column("allowed_operations", sa.JSON(), nullable=False), sa.Column("disclosure_level", sa.String(40), nullable=False), sa.Column("allow_derivation", sa.Boolean(), nullable=False, server_default=sa.false()), sa.Column("allow_disclosure_of_derivation", sa.Boolean(), nullable=False, server_default=sa.false()), sa.Column("valid_from", sa.DateTime(timezone=True), nullable=False), sa.Column("expires_at", sa.DateTime(timezone=True)), sa.Column("status", sa.String(20), nullable=False, server_default="active"), sa.Column("revoked_at", sa.DateTime(timezone=True)), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),)
    op.create_index("ix_family_consent_lookup", "family_data_consents", ["subject_patient_id", "granted_to_actor_id", "purpose_code", "status"])
    op.create_table("guardian_authorities", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("guardian_actor_id", sa.String(64), nullable=False), sa.Column("child_patient_id", sa.String(64), nullable=False), sa.Column("authority_type", sa.String(50), nullable=False), sa.Column("jurisdiction_code", sa.String(20), nullable=False), sa.Column("valid_from", sa.Date(), nullable=False), sa.Column("valid_until", sa.Date()), sa.Column("verification_status", sa.String(30), nullable=False), sa.Column("restrictions", sa.JSON(), nullable=False))
    op.create_table("jurisdiction_policies", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("jurisdiction_code", sa.String(20), nullable=False), sa.Column("policy_type", sa.String(50), nullable=False), sa.Column("threshold_age", sa.Integer()), sa.Column("effective_from", sa.Date(), nullable=False), sa.Column("effective_to", sa.Date()), sa.Column("source_uri", sa.Text(), nullable=False), sa.Column("source_version", sa.String(100), nullable=False), sa.UniqueConstraint("jurisdiction_code", "policy_type", "effective_from", name="uq_jurisdiction_policy_version"))
    op.create_table("care_transition_events", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("patient_id", sa.String(64), nullable=False), sa.Column("policy_id", sa.Integer(), sa.ForeignKey("jurisdiction_policies.id"), nullable=False), sa.Column("expected_at", sa.DateTime(timezone=True), nullable=False), sa.Column("status", sa.String(30), nullable=False, server_default="scheduled"), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))


def downgrade() -> None:
    op.drop_table("care_transition_events")
    op.drop_table("jurisdiction_policies")
    op.drop_table("guardian_authorities")
    op.drop_index("ix_family_consent_lookup", table_name="family_data_consents")
    op.drop_table("family_data_consents")
    op.drop_table("patient_node_states")
    op.drop_table("clinical_hypotheses")
    op.drop_table("health_relations")
    op.drop_table("health_nodes")
