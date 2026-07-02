from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import date, datetime


class LaboratoryInterpretation(str, enum.Enum):
    NORMAL = "normal"
    LOW = "low"
    HIGH = "high"
    CRITICAL_LOW = "critical_low"
    CRITICAL_HIGH = "critical_high"
    UNKNOWN = "unknown"


class TrendDirection(str, enum.Enum):
    UP = "up"
    DOWN = "down"
    STABLE = "stable"
    INSUFFICIENT_DATA = "insufficient_data"


@dataclass
class LaboratoryResult:
    test_name: str
    id: int | None = None
    patient_profile_id: int | None = None
    test_code: str | None = None
    value: float | None = None
    unit: str | None = None
    reference_min: float | None = None
    reference_max: float | None = None
    reference_text: str | None = None
    result_date: date | None = None
    laboratory_name: str | None = None
    notes: str | None = None
    interpretation: LaboratoryInterpretation = LaboratoryInterpretation.UNKNOWN
    created_at: datetime | None = None
    updated_at: datetime | None = None

    critical_threshold_percent: float = field(default=30.0, repr=False, compare=False)
    stable_threshold_percent: float = field(default=5.0, repr=False, compare=False)

    def __post_init__(self) -> None:
        if self.reference_min is not None and self.reference_max is not None:
            if self.reference_min > self.reference_max:
                raise ValueError(
                    f"reference_min ({self.reference_min}) не може бути більшим за "
                    f"reference_max ({self.reference_max}) для тесту {self.test_name!r}"
                )

    def has_reference_range(self) -> bool:
        return self.reference_min is not None and self.reference_max is not None

    def is_out_of_range(self) -> bool:
        if self.value is None or not self.has_reference_range():
            return False
        return self.value < self.reference_min or self.value > self.reference_max  # type: ignore[operator]

    def deviation_percent(self) -> float | None:
        """Відхилення value від найближчої порушеної межі, у відсотках.

        0.0  — значення в межах норми.
        None — недостатньо даних для розрахунку (немає value/reference range,
               або межа дорівнює 0 — відсоток від нуля не визначений).
        """
        if self.value is None or not self.has_reference_range():
            return None

        if self.value < self.reference_min:  # type: ignore[operator]
            boundary = self.reference_min
        elif self.value > self.reference_max:  # type: ignore[operator]
            boundary = self.reference_max
        else:
            return 0.0

        if boundary == 0:
            return None

        return round((self.value - boundary) / abs(boundary) * 100, 2)  # type: ignore[operator]

    def is_critical(self) -> bool:
        deviation = self.deviation_percent()
        if deviation is None:
            return False
        return abs(deviation) >= self.critical_threshold_percent

    def interpret(self) -> LaboratoryInterpretation:
        """Обчислює й записує interpretation. Єдина точка істини для статусу результату."""
        if self.value is None or not self.has_reference_range():
            self.interpretation = LaboratoryInterpretation.UNKNOWN
            return self.interpretation

        if not self.is_out_of_range():
            self.interpretation = LaboratoryInterpretation.NORMAL
            return self.interpretation

        is_low = self.value < self.reference_min  # type: ignore[operator]

        if self.is_critical():
            self.interpretation = (
                LaboratoryInterpretation.CRITICAL_LOW if is_low else LaboratoryInterpretation.CRITICAL_HIGH
            )
        else:
            self.interpretation = LaboratoryInterpretation.LOW if is_low else LaboratoryInterpretation.HIGH

        return self.interpretation

    def trend(self, previous_results: list["LaboratoryResult"]) -> TrendDirection:
        """Порівнює self з найновішим попереднім результатом того самого test_code.

        previous_results не обов'язково відсортований і може містити інші тести —
        метод сам фільтрує за test_code і бере найпізніший за result_date, що
        передує self.result_date.
        """
        if self.value is None or self.result_date is None or self.test_code is None:
            return TrendDirection.INSUFFICIENT_DATA

        comparable = [
            r
            for r in previous_results
            if r.test_code == self.test_code
            and r.value is not None
            and r.result_date is not None
            and r.result_date < self.result_date
        ]

        if not comparable:
            return TrendDirection.INSUFFICIENT_DATA

        last = max(comparable, key=lambda r: r.result_date)  # type: ignore[arg-type,return-value]

        if last.value == 0:
            return TrendDirection.INSUFFICIENT_DATA

        change_percent = (self.value - last.value) / abs(last.value) * 100  # type: ignore[operator]

        if abs(change_percent) < self.stable_threshold_percent:
            return TrendDirection.STABLE

        return TrendDirection.UP if change_percent > 0 else TrendDirection.DOWN