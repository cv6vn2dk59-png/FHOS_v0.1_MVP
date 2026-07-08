from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime


@dataclass
class Disease:
    """Факт наявності діагнозу в пацієнта в часі.

    Constitution (розділ DOMAIN): Domain не може бути Anemic Model.
    Diseases v1 дзеркалить Medications v1 (ADR-0009, ADR-0013): природа
    даних тут -- СТАН У ЧАСІ (чи діагноз активний зараз, як довго триває),
    не клінічна оцінка. resolved_date=None означає "триває дотепер"
    (хронічний стан або ще не закритий) -- та сама семантика, що вже
    працює для end_date=None у Medications; окремого статусу "chronic"
    немає (рішення користувача, S05: третій статус вимагав би нової
    логіки "хто і коли його встановлює", без Confirmed Repetition).

    Diseases v1 НЕ аналізує: протипоказання препарат-хвороба, Age-
    Typicality Score, Clinical Context Override. Усі три зафіксовані в
    FUTURE_IDEAS.md як залежні від Diseases, але жоден не має другого
    підтвердження (Confirmed Repetition, лише Confirmed Intention) --
    це майбутній Clinical Reasoning / Knowledge Asset рівень, за
    прецедентом Drug Interactions (читає facts з Diseases v1 +
    Medications v1, не змінюючи жодного з них).
    """

    diagnosis_name: str
    onset_date: date

    id: int | None = None
    patient_profile_id: int | None = None
    icd_code: str | None = None
    resolved_date: date | None = None
    notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.onset_date is not None and self.resolved_date is not None:
            if self.resolved_date < self.onset_date:
                raise ValueError(
                    f"resolved_date ({self.resolved_date}) не може бути раніше "
                    f"onset_date ({self.onset_date}) для діагнозу {self.diagnosis_name!r}"
                )

    def is_active(self, as_of: date | None = None) -> bool:
        reference_date = as_of if as_of is not None else date.today()
        return self.resolved_date is None or self.resolved_date >= reference_date

    def duration_days(self, as_of: date | None = None) -> int:
        if self.resolved_date is not None:
            return (self.resolved_date - self.onset_date).days
        reference_date = as_of if as_of is not None else date.today()
        return (reference_date - self.onset_date).days
