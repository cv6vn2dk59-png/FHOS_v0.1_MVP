from pydantic import BaseModel, Field


class MultiAIConsiliumRequest(BaseModel):
    case_id: str = Field(min_length=1, max_length=64)
    case_text: str = Field(min_length=1)
    provider_codes: list[str] = Field(min_length=1)
    clinical_context: dict = Field(default_factory=dict)
    language: str = "uk"
    require_independent_round: bool = True
    require_devil_review: bool = True
    existing_branch_ids: list[str] = Field(default_factory=list)
    facts: list[dict] = Field(default_factory=list)
    missing_evidence_ids: list[str] = Field(default_factory=list)
    safety_constraints: list[str] = Field(default_factory=list)
    timeout_seconds: int = Field(default=30, ge=1, le=300)
    mode: str = Field(default="demo")
    minimum_successful_providers: int = Field(default=2, ge=1, le=10)
    forced_failure_provider_codes: list[str] = Field(default_factory=list)
    forced_invalid_normalization_provider_codes: list[str] = Field(default_factory=list)


class MultiAIConsiliumRead(BaseModel):
    run_id: str
    case_id: str
    execution_mode: str
    is_mock: bool
    real_provider_calls: bool
    orchestration_status: str
    provider_execution_status: str
    participants: list[dict]
    rounds: list[dict]
    clinical_graph: dict
    comparison: dict
    devil_review: dict
    consensus: dict
    warnings: list[str]
    limitations: list[str]
    violations: list[str]
