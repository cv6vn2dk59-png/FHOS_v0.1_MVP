from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class MedicationCreate(BaseModel):
    patient_profile_id: int | None = None
    drug_name: str = Field(min_length=1, max_length=255)
    atc_code: str | None = Field(default=None, max_length=20)
    dose_value: float | None = None
    dose_unit: str | None = Field(default=None, max_length=50)
    dosage_text: str | None = Field(default=None, max_length=500)
    start_date: date
    end_date: date | None = None
    reason: str | None = Field(default=None, max_length=500)
    notes: str | None = None

    @model_validator(mode="after")
    def validate_dates(self) -> "MedicationCreate":
        if self.end_date is not None and self.end_date < self.start_date:
            raise ValueError("end_date не може бути раніше start_date")
        return self


class MedicationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_profile_id: int | None
    drug_name: str
    atc_code: str | None
    dose_value: float | None
    dose_unit: str | None
    dosage_text: str | None
    start_date: date
    end_date: date | None
    reason: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime