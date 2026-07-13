from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime


class EvidenceSourceType(str, enum.Enum):
    LABORATORY_RESULT = "laboratory_result"
    CLINICAL_GUIDELINE = "clinical_guideline"
    SYSTEMATIC_REVIEW = "systematic_review"
    META_ANALYSIS = "meta_analysis"
    INDIVIDUAL_STUDY = "individual_study"
    CASE_REPORT = "case_report"
    CURATED_KNOWLEDGE_BASE = "curated_knowledge_base"
    ONTOLOGY = "ontology"
    PATIENT_STATEMENT = "patient_statement"
    CLINICIAN_OBSERVATION = "clinician_observation"
    SYSTEM_INFERENCE = "system_inference"


class VerificationStatus(str, enum.Enum):
    VERIFIED = "verified"
    UNVERIFIED = "unverified"
    PARTIALLY_VERIFIED = "partially_verified"
    NOT_APPLICABLE = "not_applicable"


class EvidenceStrength(str, enum.Enum):
    DIRECT_PATIENT_FACT = "direct_patient_fact"
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"
    UNRATED = "unrated"


class HypothesisEvidenceRole(str, enum.Enum):
    SUPPORTING = "supporting"
    CONTRADICTING = "contradicting"
    CONTEXT = "context"
    NEUTRAL = "neutral"
    MISSING = "missing"


@dataclass(frozen=True)
class EvidenceSource:
    source_key: str
    source_type: EvidenceSourceType
    title: str
    uri: str | None = None
    publication_type: str | None = None
    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED
    evidence_strength: EvidenceStrength = EvidenceStrength.UNRATED
    retrieved_at: datetime | None = None
    metadata: dict = field(default_factory=dict)


@dataclass(frozen=True)
class HypothesisEvidence:
    hypothesis_key: str
    evidence_source_key: str | None
    patient_fact_id: str | None
    role: HypothesisEvidenceRole
    weight: float
    rationale: str
