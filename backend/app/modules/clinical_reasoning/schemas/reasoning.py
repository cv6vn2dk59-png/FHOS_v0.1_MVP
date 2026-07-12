from pydantic import BaseModel, Field


class HypothesisExpansionRequest(BaseModel):
    symptom_node_id: str
    user_supplied_title: str | None = None
    max_results: int = Field(default=25, ge=1, le=100)


class HypothesisRead(BaseModel):
    title: str
    mechanism: str
    origin: str
    evidence_level: str
    anatomical_source: str | None = None
    body_system: str | None = None
    etiology_category: str | None = None
    verification_questions: list[str]
    source_ids: list[str]
    status: str


class DevilReviewRead(BaseModel):
    passed: bool
    violations: list[str]
    questions: list[str]


class HypothesisExpansionRead(BaseModel):
    symptom_node_id: str
    hypotheses: list[HypothesisRead]
    devil_review: DevilReviewRead
    disclaimer: str = "Перелік клінічних гіпотез, а не встановлений діагноз."
