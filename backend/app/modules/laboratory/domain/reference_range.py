from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class ReferenceRange:
    """Референсний діапазон для одного лабораторного тесту.

    Самостійна одиниця медичного знання, НЕ властивість конкретного
    LaboratoryResult — один тест (test_code) може мати кілька
    ReferenceRange-рядків для різних комбінацій статі/віку/методу/лабораторії.
    """

    test_code: str
    test_name: str
    unit: str
    reference_min: float
    reference_max: float

    id: int | None = None
    sex: str | None = None
    age_min: int | None = None
    age_max: int | None = None
    source: str | None = None
    laboratory_name: str | None = None
    method: str | None = None
    is_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.reference_min > self.reference_max:
            raise ValueError(
                f"reference_min ({self.reference_min}) не може бути більшим за "
                f"reference_max ({self.reference_max}) для {self.test_code!r}"
            )

    def has_age_restriction(self) -> bool:
        return self.age_min is not None or self.age_max is not None

    def matches(
        self,
        *,
        test_code: str,
        unit: str,
        sex: str | None = None,
        age: int | None = None,
        laboratory_name: str | None = None,
        method: str | None = None,
    ) -> bool:
        """Чи підходить цей ReferenceRange під контекст пацієнта/тесту.

        Правила (ReferenceRangeResolver v1):
        - test_code і unit: обов'язковий точний збіг, конвертація одиниць
          не виконується в v1.
        - sex / laboratory_name / method: range-поле None -> "загальний"
          діапазон, підходить під будь-яке значення контексту. Range-поле
          задане -> має точно співпасти; якщо контекст невідомий (None),
          такий діапазон НЕ підходить (не вгадуємо).
        - вік: обидва age_min/age_max відсутні -> без вікового обмеження,
          підходить завжди. Хоча б одне задане -> контекстний age має
          потрапляти в межі (відсутня межа = -inf/+inf); якщо контекстний
          age невідомий (None) -> діапазон НЕ підходить.
        """
        if self.test_code != test_code or self.unit != unit:
            return False

        if not self._matches_nullable_field(self.sex, sex):
            return False

        if not self._matches_nullable_field(self.laboratory_name, laboratory_name):
            return False

        if not self._matches_nullable_field(self.method, method):
            return False

        if self.has_age_restriction():
            if age is None:
                return False
            effective_min = self.age_min if self.age_min is not None else float("-inf")
            effective_max = self.age_max if self.age_max is not None else float("inf")
            if not (effective_min <= age <= effective_max):
                return False

        return True

    @staticmethod
    def _matches_nullable_field(range_value: str | None, context_value: str | None) -> bool:
        if range_value is None:
            return True
        return range_value == context_value

    def specificity_score(self) -> int:
        """Структурна специфічність діапазону — НЕ залежить від контексту пацієнта.

        Використовується Resolver'ом для вибору найбільш специфічного серед
        кількох підходящих діапазонів (правило: male+age+method виграє над
        male+age, виграє над default-діапазоном без жодних обмежень).
        """
        score = 0
        if self.sex is not None:
            score += 1
        if self.has_age_restriction():
            score += 1
        if self.laboratory_name is not None:
            score += 1
        if self.method is not None:
            score += 1
        return score

    def is_default(self) -> bool:
        """Діапазон без жодних специфічних обмежень — fallback-кандидат."""
        return self.specificity_score() == 0