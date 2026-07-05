from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime


@dataclass
class Medication:
    """Факт прийому препарату пацієнтом.

    Constitution (розділ DOMAIN): Domain не може бути Anemic Model.
    Природа медичних даних тут інша, ніж у Laboratory (обчислення) чи
    Imaging (опис документа) - Medications описує СТАН У ЧАСІ (чи
    людина зараз приймає препарат, як довго приймає). Domain-логіка
    відповідно тонша, ніж Laboratory, і зосереджена на часових
    обчисленнях, не на клінічній оцінці.

    Medications v1 НЕ аналізує: взаємодії препаратів, ризики, зв'язок
    з Laboratory/Diseases, ефективність терапії. Це майбутній Clinical
    Reasoning / Knowledge Asset рівень (Three Levels of Thinking,
    FUTURE_IDEAS.md) - жодна логіка тут не повинна вимагати даних
    іншого медичного модуля.
    """

    drug_name: str
    start_date: date

    id: int | None = None
    patient_profile_id: int | None = None
    atc_code: str | None = None
    dose_value: float | None = None
    dose_unit: str | None = None
    dosage_text: str | None = None
    end_date: date | None = None
    reason: str | None = None
    notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.start_date is not None and self.end_date is not None:
            if self.end_date < self.start_date:
                raise ValueError(
                    f"end_date ({self.end_date}) не може бути раніше "
                    f"start_date ({self.start_date}) для препарату {self.drug_name!r}"
                )

    def is_active(self, as_of: date | None = None) -> bool:
        reference_date = as_of if as_of is not None else date.today()
        return self.end_date is None or self.end_date >= reference_date

    def duration_days(self, as_of: date | None = None) -> int:
        if self.end_date is not None:
            return (self.end_date - self.start_date).days
        reference_date = as_of if as_of is not None else date.today()
        return (reference_date - self.start_date).days