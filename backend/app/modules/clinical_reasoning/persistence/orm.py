from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.persistence.base import Base


class HealthNodeORM(Base):
    __tablename__ = "health_nodes"
    id: Mapped[int] = mapped_column(primary_key=True)
    external_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    external_source: Mapped[str] = mapped_column(String(50), nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    node_kind: Mapped[str] = mapped_column(String(50), nullable=False)


class HealthRelationORM(Base):
    __tablename__ = "health_relations"
    id: Mapped[int] = mapped_column(primary_key=True)
    from_node_id: Mapped[str] = mapped_column(String(255), ForeignKey("health_nodes.external_id", ondelete="CASCADE"), nullable=False)
    to_node_id: Mapped[str] = mapped_column(String(255), ForeignKey("health_nodes.external_id", ondelete="CASCADE"), nullable=False)
    relation_kind: Mapped[str] = mapped_column(String(50), nullable=False)
    evidence_level: Mapped[str] = mapped_column(String(50), nullable=False)
    source_citation: Mapped[str] = mapped_column(Text, nullable=False)
    is_directed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    __table_args__ = (UniqueConstraint("from_node_id", "to_node_id", "relation_kind", "source_citation", name="uq_health_relation_evidence"),)


class ClinicalHypothesisORM(Base):
    __tablename__ = "clinical_hypotheses"
    id: Mapped[int] = mapped_column(primary_key=True)
    symptom_node_id: Mapped[str] = mapped_column(String(255), ForeignKey("health_nodes.external_id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    mechanism: Mapped[str] = mapped_column(Text, nullable=False)
    origin: Mapped[str] = mapped_column(String(30), nullable=False)
    evidence_level: Mapped[str] = mapped_column(String(50), nullable=False)
    anatomical_source: Mapped[str | None] = mapped_column(String(255))
    body_system: Mapped[str | None] = mapped_column(String(100))
    etiology_category: Mapped[str | None] = mapped_column(String(100))
    verification_questions: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    supporting_evidence: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    contradicting_evidence: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    missing_evidence: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    source_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="candidate_hypotheses")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class PatientNodeStateORM(Base):
    __tablename__ = "patient_node_states"
    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[str] = mapped_column(String(64), nullable=False)
    node_id: Mapped[str] = mapped_column(String(255), ForeignKey("health_nodes.external_id", ondelete="CASCADE"), nullable=False)
    episode_id: Mapped[str] = mapped_column(String(64), nullable=False)
    activated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    family_link_reason: Mapped[str | None] = mapped_column(String(100))
    __table_args__ = (UniqueConstraint("patient_id", "node_id", "episode_id", name="uq_patient_node_episode"),)


class ConsentEnvelopeORM(Base):
    __tablename__ = "family_data_consents"
    id: Mapped[int] = mapped_column(primary_key=True)
    subject_patient_id: Mapped[str] = mapped_column(String(64), nullable=False)
    granted_to_actor_id: Mapped[str] = mapped_column(String(64), nullable=False)
    purpose_code: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_node_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    allowed_operations: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    disclosure_level: Mapped[str] = mapped_column(String(40), nullable=False)
    allow_derivation: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    allow_disclosure_of_derivation: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    __table_args__ = (Index("ix_family_consent_lookup", "subject_patient_id", "granted_to_actor_id", "purpose_code", "status"),)


class GuardianAuthorityORM(Base):
    __tablename__ = "guardian_authorities"
    id: Mapped[int] = mapped_column(primary_key=True)
    guardian_actor_id: Mapped[str] = mapped_column(String(64), nullable=False)
    child_patient_id: Mapped[str] = mapped_column(String(64), nullable=False)
    authority_type: Mapped[str] = mapped_column(String(50), nullable=False)
    jurisdiction_code: Mapped[str] = mapped_column(String(20), nullable=False)
    valid_from: Mapped[date] = mapped_column(Date, nullable=False)
    valid_until: Mapped[date | None] = mapped_column(Date)
    verification_status: Mapped[str] = mapped_column(String(30), nullable=False, default="verified")
    restrictions: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)


class JurisdictionPolicyORM(Base):
    __tablename__ = "jurisdiction_policies"
    id: Mapped[int] = mapped_column(primary_key=True)
    jurisdiction_code: Mapped[str] = mapped_column(String(20), nullable=False)
    policy_type: Mapped[str] = mapped_column(String(50), nullable=False)
    threshold_age: Mapped[int | None] = mapped_column(Integer)
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[date | None] = mapped_column(Date)
    source_uri: Mapped[str] = mapped_column(Text, nullable=False)
    source_version: Mapped[str] = mapped_column(String(100), nullable=False)
    __table_args__ = (UniqueConstraint("jurisdiction_code", "policy_type", "effective_from", name="uq_jurisdiction_policy_version"),)


class CareTransitionEventORM(Base):
    __tablename__ = "care_transition_events"
    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[str] = mapped_column(String(64), nullable=False)
    policy_id: Mapped[int] = mapped_column(ForeignKey("jurisdiction_policies.id"), nullable=False)
    expected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="scheduled")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
