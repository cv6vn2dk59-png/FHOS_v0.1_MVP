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


class ConsiliumRoleInput(BaseModel):
    code: str
    title: str
    focus_domains: list[str] = Field(default_factory=list)
    devil_role: bool = False


class BranchReviewInput(BaseModel):
    role_code: str
    branch_id: str
    position: str
    rationale: str
    evidence_ids: list[str] = Field(default_factory=list)
    requested_evidence_ids: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0, le=1)
    provenance: list[ProvenanceInput] = Field(min_length=1)


class DynamicConsiliumRequest(BaseModel):
    case_id: str = Field(min_length=1, max_length=64)
    branches: list[BranchInput] = Field(min_length=1)
    roles: list[ConsiliumRoleInput] = Field(min_length=1)
    reviews: list[BranchReviewInput] = Field(default_factory=list)
    cluster_branch_ids: list[list[str]] = Field(default_factory=list)


class DynamicConsiliumRead(BaseModel):
    case_id: str
    branch_reviews: list[dict]
    consensus: dict
    violations: list[dict]
    warnings: list[str]
    limitations: list[str]
    disclaimer: str = "Consensus is not a diagnosis; minority opinions and alternative branches remain visible."
