from __future__ import annotations

import enum
from dataclasses import dataclass
from datetime import date, datetime


class ImagingStudyType(str, enum.Enum):
    XRAY = "xray"
    CT = "ct"
    MRI = "mri"
    ULTRASOUND = "ultrasound"
    MAMMOGRAPHY = "mammography"
    OTHER = "other"


@dataclass
class ImagingStudy:
    """Архів медичного висновку з дослідження (рентген, КТ, МРТ, УЗД тощо).

    Тонкий Domain v1: система зберігає текстовий висновок лікаря, не
    інтерпретує його. Клінічна оцінка належить лікарю, що написав
    висновок — не FHOS. Немає reference range/score для зображень
    (немає підтвердженої потреби структурувати цей вид знання, YAGNI).
    """

    study_type: ImagingStudyType
    body_part: str
    study_date: date

    id: int | None = None
    patient_profile_id: int | None = None
    facility_name: str | None = None
    radiologist_conclusion: str | None = None
    image_file_path: str | None = None
    notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def has_conclusion(self) -> bool:
        return self.radiologist_conclusion is not None and self.radiologist_conclusion.strip() != ""

    def has_image_file(self) -> bool:
        return self.image_file_path is not None and self.image_file_path.strip() != ""

    def days_since_study(self, as_of: date | None = None) -> int:
        reference_date = as_of if as_of is not None else date.today()
        return (reference_date - self.study_date).days