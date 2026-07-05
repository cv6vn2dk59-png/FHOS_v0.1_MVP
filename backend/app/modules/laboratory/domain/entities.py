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


class ReferenceRangeStatus(str, enum.Enum):
    MANUAL = "manual"
    RESOLVED = "resolved"
    NOT_FOUND = "not_found"


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
    reference_range_status: ReferenceRangeStatus | None = None
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

    def has_lower_bound(self) -> bool:
        return self.reference_min is not None

    def has_upper_bound(self) -> bool:
        return self.reference_max is not None

    def has_reference_range(self) -> bool:
        return self.has_lower_bound() or self.has_upper_bound()

    def is_out_of_range(self) -> bool:
        if self.value is None or not self.has_reference_range():
            return False
        if self.has_lower_bound() and self.value < self.reference_min:
            return True
        if self.has_upper_bound() and self.value > self.reference_max:
            return True
        return False

    def deviation_percent(self) -> float | None:
        if self.value is None or not self.has_reference_range():
            return None

        if self.has_lower_bound() and self.value < self.reference_min:
            boundary = self.reference_min
        elif self.has_upper_bound() and self.value > self.reference_max:
            boundary = self.reference_max
        else:
            return 0.0

        if boundary == 0:
            return None
        return round((self.value - boundary) / abs(boundary) * 100, 2)

    def is_critical(self) -> bool:
        deviation = self.deviation_percent()
        if deviation is None:
            return False
        return abs(deviation) >= self.critical_threshold_percent

    def interpret(self) -> LaboratoryInterpretation:
        if self.value is None or not self.has_reference_range():
            self.interpretation = LaboratoryInterpretation.UNKNOWN
            return self.interpretation

        if not self.is_out_of_range():
            self.interpretation = LaboratoryInterpretation.NORMAL
            return self.interpretation

        is_low = self.has_lower_bound() and self.value < self.reference_min

        if self.is_critical():
            self.interpretation = (
                LaboratoryInterpretation.CRITICAL_LOW if is_low else LaboratoryInterpretation.CRITICAL_HIGH
            )
        else:
            self.interpretation = LaboratoryInterpretation.LOW if is_low else LaboratoryInterpretation.HIGH

        return self.interpretation

    def trend(self, previous_results: list["LaboratoryResult"]) -> TrendDirection:
        if self.value is None or self.result_date is None or self.test_code is None:
            return TrendDirection.INSUFFICIENT_DATA

        comparable = [
            r for r in previous_results
            if r.test_code == self.test_code and r.value is not None
            and r.result_date is not None and r.result_date < self.result_date
        ]

        if not comparable:
            return TrendDirection.INSUFFICIENT_DATA

        last = max(comparable, key=lambda r: r.result_date)

        if last.value == 0:
            return TrendDirection.INSUFFICIENT_DATA

        change_percent = (self.value - last.value) / abs(last.value) * 100

        if abs(change_percent) < self.stable_threshold_percent:
            return TrendDirection.STABLE

        return TrendDirection.UP if change_percent > 0 else TrendDirection.DOWN

    def abnormality_score(self) -> float | None:
        deviation = self.deviation_percent()
        if deviation is None:
            return None

        abs_deviation = abs(deviation)

        if abs_deviation == 0:
            return 0.0
        if abs_deviation <= 10:
            return 0.25
        if abs_deviation <= 30:
            return 0.5
        if abs_deviation <= 50:
            return 0.75
        return 1.0
