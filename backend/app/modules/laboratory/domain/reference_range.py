from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class ReferenceRange:
    test_code: str
    test_name: str
    unit: str

    id: int | None = None
    reference_min: float | None = None
    reference_max: float | None = None
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
        if self.reference_min is None and self.reference_max is None:
            raise ValueError(
                f"ReferenceRange для {self.test_code!r} повинен мати хоча б одну межу "
                f"(reference_min або reference_max)"
            )
        if self.reference_min is not None and self.reference_max is not None:
            if self.reference_min > self.reference_max:
                raise ValueError(
                    f"reference_min ({self.reference_min}) не може бути більшим за "
                    f"reference_max ({self.reference_max}) для {self.test_code!r}"
                )

    def has_age_restriction(self) -> bool:
        return self.age_min is not None or self.age_max is not None

    def matches(
        self, *, test_code: str, unit: str, sex: str | None = None, age: int | None = None,
        laboratory_name: str | None = None, method: str | None = None,
    ) -> bool:
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
        return self.specificity_score() == 0