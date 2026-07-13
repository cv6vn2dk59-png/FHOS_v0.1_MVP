from pydantic import BaseModel, Field


class ProvenanceRead(BaseModel):
    source_id: str
    source_version: str
    locator: str | None = None


class BranchEvidenceEffectInput(BaseModel):
    branch_id: str
    possible_result: str
    effect_type: str
    expected_strength: float = Field(ge=0, le=1)


class EvidenceCandidateInput(BaseModel):
    id: str
    proposed_data_item: str
    evidence_type: str
    affected_branch_ids: list[str]
    effects: list[BranchEvidenceEffectInput]
    evidence_reliability: float = Field(ge=0, le=1)
    context_applicability: float = Field(ge=0, le=1)
    clinical_utility: float = Field(ge=0, le=1)
    safety_priority: float = Field(ge=0, le=1)
    time_sensitivity: float = Field(ge=0, le=1)
    invasiveness: float = Field(ge=0, le=1)
    cost_burden: float = Field(ge=0, le=1)
    actionability: float = Field(ge=0, le=1)
    provenance: list[ProvenanceRead]
    limitations: list[str] = Field(default_factory=list)


class HypothesisBranchInput(BaseModel):
    id: str
    case_id: str
    title: str
    description: str
    root_trigger_ids: list[str]
    causal_domain: str
    branch_type: str
    node_ids: list[str]
    edge_ids: list[str]
    supporting_fact_ids: list[str] = Field(default_factory=list)
    contradicting_fact_ids: list[str] = Field(default_factory=list)
    neutral_fact_ids: list[str] = Field(default_factory=list)
    missing_evidence_ids: list[str] = Field(default_factory=list)
    evidence_strength: str = "plausible"
    confidence: float = Field(default=0.5, ge=0, le=1)
    status: str = "generated"
    provenance: list[ProvenanceRead]
    context_constraints: list[dict] = Field(default_factory=list)
    safety_critical: bool = False


class BranchDiscriminationRequest(BaseModel):
    case_id: str = Field(min_length=1, max_length=64)
    branches: list[HypothesisBranchInput] = Field(min_length=2)
    candidates: list[EvidenceCandidateInput] = Field(default_factory=list)


class BranchDiscriminationRead(BaseModel):
    case_id: str
    comparisons: list[dict]
    ranked_candidates: list[dict]
    unresolved_branch_pairs: list[list[str]]
    limitations: list[str]
    warnings: list[str]
    disclaimer: str = (
        "Information gain and priority are decision-support heuristics, not diagnosis probabilities or risk scores."
    )
