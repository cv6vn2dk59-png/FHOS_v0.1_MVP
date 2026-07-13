from pydantic import BaseModel, Field


class ClinicalCausalityRequest(BaseModel):
    patient_id: str = Field(min_length=1, max_length=64)
    episode_id: str = Field(min_length=1, max_length=64)
    result_ids: list[int] = Field(min_length=1)
    persist: bool = True


class CausalityBranchRead(BaseModel):
    code: str
    title: str
    patient_fact_ids: list[str]
    functional_processes: list[str]
    body_systems: list[str]
    mechanisms: list[dict]
    candidate_hypotheses: list[str]
    possible_consequences: list[str]
    missing_evidence: list[str]
    alternative_mechanisms: list[str]
    prohibited_conclusions: list[str]


class ClinicalCausalityRead(BaseModel):
    patient_id: str
    episode_id: str
    observations: list[dict]
    branches: list[CausalityBranchRead]
    unassigned_fact_ids: list[str]
    devil_review: dict
    disclaimer: str = "Причинні гілки є кандидатними поясненнями, а не підтвердженими діагнозами."
