from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.modules.laboratory.domain.entities import (
    LaboratoryInterpretation,
    ReferenceRangeStatus,
    TrendDirection,
)


class LaboratoryResultCreate(BaseModel):
    patient_profile_id: int | None = None
    test_name: str = Field(min_length=1, max_length=255)
    test_code: str | None = Field(default=None, max_length=100)
    value: float | None = None
    unit: str | None = Field(default=None, max_length=50)
    reference_min: float | None = None
    reference_max: float | None = None
    reference_text: str | None = Field(default=None, max_length=255)
    result_date: date | None = None
    laboratory_name: str | None = Field(default=None, max_length=255)
    method: str | None = Field(default=None, max_length=100)
    notes: str | None = None

    @model_validator(mode="after")
    def validate_reference_range(self) -> "LaboratoryResultCreate":
        if self.reference_min is not None and self.reference_max is not None:
            if self.reference_min > self.reference_max:
                raise ValueError("reference_min не може бути більшим за reference_max")
        return self


class LaboratoryResultRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_profile_id: int | None
    test_name: str
    test_code: str | None
    value: float | None
    unit: str | None
    reference_min: float | None
    reference_max: float | None
    reference_text: str | None
    result_date: date | None
    laboratory_name: str | None
    notes: str | None
    interpretation: LaboratoryInterpretation
    reference_range_status: ReferenceRangeStatus | None
    created_at: datetime
    updated_at: datetime


class LaboratoryTrendRead(BaseModel):
    patient_profile_id: int
    test_code: str
    latest_value: float | None
    latest_interpretation: LaboratoryInterpretation
    trend: TrendDirection