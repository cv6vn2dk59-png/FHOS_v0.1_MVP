from pydantic import BaseModel, Field


class StructuredConsiliumRequest(BaseModel):
    patient_id: str = Field(min_length=1, max_length=64)
    episode_id: str = Field(min_length=1, max_length=64)
    result_ids: list[int] = Field(min_length=1)
    persist: bool = True


class EvidenceReferenceRead(BaseModel):
    laboratory_result_id: int
    test_code: str
    role: str
    rationale: str


class CandidateHypothesisRead(BaseModel):
    code: str
    title: str
    status: str
    evidence: list[EvidenceReferenceRead]
    missing_evidence: list[str]
    prohibited_conclusions: list[str]


class DomainReaderReportRead(BaseModel):
    specialty: str
    observed_fact_ids: list[int]
    candidate_hypotheses: list[CandidateHypothesisRead]
    questions: list[str]
    confidence: str
    prohibited_conclusions: list[str]


class StructuredConsiliumRead(BaseModel):
    patient_id: str
    episode_id: str
    observations: list[dict]
    domain_reports: list[DomainReaderReportRead]
    consensus: dict
    devil_review: dict
    disclaimer: str = "Структурований консиліум формує кандидатні напрямки, а не встановлює діагноз."
