from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class DiseaseCreate(BaseModel):
    patient_profile_id: int | None = None
    diagnosis_name: str = Field(min_length=1, max_length=255)
    icd_code: str | None = Field(default=None, max_length=20)
    onset_date: date
    resolved_date: date | None = None
    notes: str | None = None

    @model_validator(mode="after")
    def validate_dates(self) -> "DiseaseCreate":
        # Навмисне дублювання Disease.__post_init__ (domain-інваріант) --
        # fail-fast на межі API з 422 замість того, щоб дійти до domain-шару
        # і впасти там з менш зрозумілою помилкою. Той самий клас
        # duplication, що вже задокументований для
        # LaboratoryResultCreate.validate_reference_range() (PROJECT_STATE.md
        # backlog) -- тут одразу з явним коментарем, а не залишено мовчки.
        if self.resolved_date is not None and self.resolved_date < self.onset_date:
            raise ValueError("resolved_date не може бути раніше onset_date")
        return self


class DiseaseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_profile_id: int | None
    diagnosis_name: str
    icd_code: str | None
    onset_date: date
    resolved_date: date | None
    notes: str | None
    created_at: datetime
    updated_at: datetime
