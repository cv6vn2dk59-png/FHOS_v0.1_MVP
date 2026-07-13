from pydantic import BaseModel, Field


class LaboratoryProfileRequest(BaseModel):
    patient_id: str = Field(min_length=1, max_length=64)
    episode_id: str = Field(min_length=1, max_length=64)
    result_ids: list[int] = Field(min_length=1)
    persist: bool = True


class LaboratoryObservationRead(BaseModel):
    laboratory_result_id: int
    patient_id: str
    episode_id: str
    node_id: str
    test_code: str
    test_name: str
    value: float | None
    unit: str | None
    reference_min: float | None
    reference_max: float | None
    critical_low: float | None
    critical_high: float | None
    interpretation: str
    observation_class: str
    evidence_role: str
    result_date: str | None
    provenance: dict


class ReviewDomainRead(BaseModel):
    code: str
    title: str
    status: str
    evidence_result_ids: list[int]
    signal_result_ids: list[int]
    context_result_ids: list[int]


class LaboratoryProfileRead(BaseModel):
    patient_id: str
    episode_id: str
    observations: list[LaboratoryObservationRead]
    review_domains: list[ReviewDomainRead]
    devil_review: dict
    disclaimer: str = (
        "Повний лабораторний профіль для клінічного обговорення; "
        "нормальні результати не відкидаються, а відхилення не є діагнозом."
    )
