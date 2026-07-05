from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.modules.imaging.domain.entities import ImagingStudyType


class ImagingStudyCreate(BaseModel):
    patient_profile_id: int | None = None
    study_type: ImagingStudyType
    body_part: str = Field(min_length=1, max_length=255)
    study_date: date
    facility_name: str | None = Field(default=None, max_length=255)
    radiologist_conclusion: str | None = None
    image_file_path: str | None = Field(default=None, max_length=500)
    notes: str | None = None


class ImagingStudyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_profile_id: int | None
    study_type: ImagingStudyType
    body_part: str
    study_date: date
    facility_name: str | None
    radiologist_conclusion: str | None
    image_file_path: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime