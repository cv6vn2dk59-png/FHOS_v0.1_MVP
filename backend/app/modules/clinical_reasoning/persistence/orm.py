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


class LaboratoryGraphObservationORM(Base):
    __tablename__ = "laboratory_graph_observations"

    id: Mapped[int] = mapped_column(primary_key=True)
    laboratory_result_id: Mapped[int] = mapped_column(
        ForeignKey("laboratory_results.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    patient_node_state_id: Mapped[int] = mapped_column(
        ForeignKey("patient_node_states.id", ondelete="CASCADE"), nullable=False
    )
    patient_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    episode_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    node_id: Mapped[str] = mapped_column(
        String(255), ForeignKey("health_nodes.external_id", ondelete="CASCADE"), nullable=False
    )
    test_code: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[float | None] = mapped_column()
    unit: Mapped[str | None] = mapped_column(String(50))
    reference_min: Mapped[float | None] = mapped_column()
    reference_max: Mapped[float | None] = mapped_column()
    critical_low: Mapped[float | None] = mapped_column()
    critical_high: Mapped[float | None] = mapped_column()
    interpretation: Mapped[str] = mapped_column(String(30), nullable=False)
    observation_class: Mapped[str] = mapped_column(String(30), nullable=False)
    evidence_role: Mapped[str] = mapped_column(String(20), nullable=False)
    result_date: Mapped[date | None] = mapped_column(Date)
    provenance: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        Index("ix_lab_graph_observation_patient_episode", "patient_id", "episode_id"),
    )

class CausalGraphNodeORM(Base):
    __tablename__ = "causal_graph_nodes"
    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    external_node_id: Mapped[str] = mapped_column(String(255), nullable=False)
    node_kind: Mapped[str] = mapped_column(String(50), nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    __table_args__ = (UniqueConstraint("case_id", "external_node_id", name="uq_causal_node_case_external"),)


class CausalGraphEdgeORM(Base):
    __tablename__ = "causal_graph_edges"
    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    source_node_id: Mapped[str] = mapped_column(String(255), nullable=False)
    target_node_id: Mapped[str] = mapped_column(String(255), nullable=False)
    relation_type: Mapped[str] = mapped_column(String(80), nullable=False)
    evidence_strength: Mapped[str] = mapped_column(String(40), nullable=False)
    confidence: Mapped[float] = mapped_column(nullable=False)
    provenance: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    context_constraints: Mapped[list] = mapped_column(JSON, nullable=False, default=list)


class HypothesisBranchORM(Base):
    __tablename__ = "hypothesis_branches"
    id: Mapped[int] = mapped_column(primary_key=True)
    branch_uid: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    case_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    causal_domain: Mapped[str] = mapped_column(String(100), nullable=False)
    branch_type: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="generated")
    root_trigger_ids: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    node_ids: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    edge_ids: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    supporting_fact_ids: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    contradicting_fact_ids: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    neutral_fact_ids: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    missing_evidence_ids: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    evidence_strength: Mapped[str] = mapped_column(String(40), nullable=False)
    confidence: Mapped[float] = mapped_column(nullable=False)
    provenance: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    context_constraints: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    safety_critical: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class BranchRelationshipORM(Base):
    __tablename__ = "branch_relationships"
    id: Mapped[int] = mapped_column(primary_key=True)
    relationship_uid: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    case_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    source_branch_uid: Mapped[str] = mapped_column(String(128), nullable=False)
    target_branch_uid: Mapped[str] = mapped_column(String(128), nullable=False)
    relationship_type: Mapped[str] = mapped_column(String(80), nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_strength: Mapped[str] = mapped_column(String(40), nullable=False)
    confidence: Mapped[float] = mapped_column(nullable=False)
    provenance: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    context_constraints: Mapped[list] = mapped_column(JSON, nullable=False, default=list)


class EvidenceSourceORM(Base):
    __tablename__ = "evidence_sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_key: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    uri: Mapped[str | None] = mapped_column(Text)
    publication_type: Mapped[str | None] = mapped_column(String(100))
    verification_status: Mapped[str] = mapped_column(String(40), nullable=False)
    evidence_strength: Mapped[str] = mapped_column(String(40), nullable=False)
    retrieved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    source_metadata: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )


class HypothesisEvidenceORM(Base):
    __tablename__ = "hypothesis_evidence"

    id: Mapped[int] = mapped_column(primary_key=True)
    hypothesis_key: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    evidence_source_id: Mapped[int] = mapped_column(
        ForeignKey("evidence_sources.id", ondelete="CASCADE"), nullable=False
    )
    patient_fact_id: Mapped[str | None] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(40), nullable=False)
    weight: Mapped[float] = mapped_column(nullable=False, default=1.0)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        UniqueConstraint(
            "hypothesis_key",
            "evidence_source_id",
            "patient_fact_id",
            "role",
            name="uq_hypothesis_evidence_assignment",
        ),
    )


class PatientCausalityAssessmentORM(Base):
    __tablename__ = "patient_causality_assessments"

    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    episode_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    input_result_ids: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    assessment_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        UniqueConstraint("patient_id", "episode_id", name="uq_patient_causality_episode"),
    )


class BranchComparisonORM(Base):
    __tablename__ = "branch_comparisons"

    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    branch_a_uid: Mapped[str] = mapped_column(String(128), nullable=False)
    branch_b_uid: Mapped[str] = mapped_column(String(128), nullable=False)
    shared_fact_ids: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    differentiating_fact_ids: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    conflicting_fact_ids: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    missing_discriminator_ids: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    relationship_type: Mapped[str] = mapped_column(String(80), nullable=False)
    comparison_summary: Mapped[str] = mapped_column(Text, nullable=False)
    metric_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        UniqueConstraint("case_id", "branch_a_uid", "branch_b_uid", name="uq_branch_comparison_pair"),
    )


class EvidenceCandidateORM(Base):
    __tablename__ = "evidence_candidates"

    id: Mapped[int] = mapped_column(primary_key=True)
    candidate_uid: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    case_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    proposed_data_item: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_type: Mapped[str] = mapped_column(String(80), nullable=False)
    affected_branch_ids: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    score_inputs: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    information_gain: Mapped[float] = mapped_column(nullable=False)
    priority_score: Mapped[float] = mapped_column(nullable=False)
    provenance: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    limitations: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )


class EvidenceCandidateEffectORM(Base):
    __tablename__ = "evidence_candidate_effects"

    id: Mapped[int] = mapped_column(primary_key=True)
    candidate_id: Mapped[int] = mapped_column(
        ForeignKey("evidence_candidates.id", ondelete="CASCADE"), nullable=False, index=True
    )
    branch_uid: Mapped[str] = mapped_column(String(128), nullable=False)
    possible_result: Mapped[str] = mapped_column(Text, nullable=False)
    effect_type: Mapped[str] = mapped_column(String(50), nullable=False)
    expected_strength: Mapped[float] = mapped_column(nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "candidate_id", "branch_uid", "possible_result", "effect_type",
            name="uq_evidence_candidate_effect",
        ),
    )


class ClinicalTimelineEventORM(Base):
    __tablename__ = "clinical_timeline_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_uid: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    case_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    event_kind: Mapped[str] = mapped_column(String(50), nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    temporal_interval: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    precision: Mapped[str] = mapped_column(String(30), nullable=False, default="unknown")
    branch_ids: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    provenance: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    context_json: Mapped[dict] = mapped_column("context", JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class TemporalRelationORM(Base):
    __tablename__ = "temporal_relations"

    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    source_event_uid: Mapped[str] = mapped_column(String(128), nullable=False)
    target_event_uid: Mapped[str] = mapped_column(String(128), nullable=False)
    relation_kind: Mapped[str] = mapped_column(String(40), nullable=False)
    certainty: Mapped[float] = mapped_column(nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    __table_args__ = (UniqueConstraint("case_id", "source_event_uid", "target_event_uid", name="uq_temporal_relation_pair"),)


class TemporalConflictORM(Base):
    __tablename__ = "temporal_conflicts"

    id: Mapped[int] = mapped_column(primary_key=True)
    conflict_uid: Mapped[str] = mapped_column(String(160), nullable=False, unique=True)
    case_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    link_uid: Mapped[str] = mapped_column(String(128), nullable=False)
    conflict_type: Mapped[str] = mapped_column(String(60), nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    source_event_uid: Mapped[str] = mapped_column(String(128), nullable=False)
    target_event_uid: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class MissingTemporalEvidenceORM(Base):
    __tablename__ = "missing_temporal_evidence"

    id: Mapped[int] = mapped_column(primary_key=True)
    missing_uid: Mapped[str] = mapped_column(String(160), nullable=False, unique=True)
    case_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    event_ids: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class MechanisticClusterORM(Base):
    __tablename__ = "mechanistic_clusters_v2"

    id: Mapped[int] = mapped_column(primary_key=True)
    cluster_uid: Mapped[str] = mapped_column(String(180), nullable=False, unique=True)
    case_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    cluster_type: Mapped[str] = mapped_column(String(80), nullable=False)
    branch_ids: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    body_systems: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    shared_item_ids: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    evidence_strength: Mapped[str] = mapped_column(String(40), nullable=False)
    confidence: Mapped[float] = mapped_column(nullable=False)
    provenance: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    context_constraints: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    member_branches_preserved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class MechanisticClusterConflictORM(Base):
    __tablename__ = "mechanistic_cluster_conflicts"

    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    cluster_uid: Mapped[str | None] = mapped_column(String(180), nullable=True)
    conflict_code: Mapped[str] = mapped_column(String(100), nullable=False)
    branch_ids: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
