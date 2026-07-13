from pydantic import BaseModel, Field


class ProvenanceInput(BaseModel):
    source_id: str
    source_version: str
    locator: str | None = None


class BranchInput(BaseModel):
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
    provenance: list[ProvenanceInput] = Field(min_length=1)
    context_constraints: list[dict] = Field(default_factory=list)
    safety_critical: bool = False


class MechanisticProfileInput(BaseModel):
    branch_id: str
    body_systems: list[str] = Field(min_length=1)
    upstream_mechanism_ids: list[str] = Field(default_factory=list)
    downstream_consequence_ids: list[str] = Field(default_factory=list)
    risk_factor_ids: list[str] = Field(default_factory=list)
    provenance: list[ProvenanceInput] = Field(min_length=1)
    context_constraints: list[dict] = Field(default_factory=list)


class MechanisticClusteringRequest(BaseModel):
    case_id: str = Field(min_length=1, max_length=64)
    branches: list[BranchInput] = Field(min_length=1)
    profiles: list[MechanisticProfileInput] = Field(min_length=1)


class MechanisticClusteringRead(BaseModel):
    case_id: str
    clusters: list[dict]
    conflicts: list[dict]
    independent_branch_ids: list[str]
    limitations: list[str]
    warnings: list[str]
    disclaimer: str = "A mechanistic cluster is not a diagnosis and does not replace its member branches."
