from datetime import date

import pytest

from app.modules.laboratory.domain.entities import (
    LaboratoryInterpretation,
    LaboratoryResult,
    TrendDirection,
)


def make_result(**overrides) -> LaboratoryResult:
    defaults = dict(
        test_name="Glucose",
        test_code="GLU",
        value=5.0,
        unit="mmol/L",
        reference_min=3.9,
        reference_max=5.5,
        result_date=date(2026, 1, 1),
    )
    defaults.update(overrides)
    return LaboratoryResult(**defaults)


class TestReferenceRangeValidation:
    def test_raises_when_min_greater_than_max(self):
        with pytest.raises(ValueError):
            make_result(reference_min=10, reference_max=5)


class TestIsOutOfRange:
    def test_within_range_is_not_out_of_range(self):
        assert make_result(value=4.5).is_out_of_range() is False

    def test_below_min_is_out_of_range(self):
        assert make_result(value=2.0).is_out_of_range() is True

    def test_above_max_is_out_of_range(self):
        assert make_result(value=7.0).is_out_of_range() is True

    def test_missing_value_is_not_out_of_range(self):
        assert make_result(value=None).is_out_of_range() is False

    def test_missing_reference_range_is_not_out_of_range(self):
        assert make_result(reference_min=None, reference_max=None).is_out_of_range() is False


class TestDeviationPercent:
    def test_within_range_deviation_is_zero(self):
        assert make_result(value=4.5).deviation_percent() == 0.0

    def test_below_min_deviation_is_negative(self):
        result = make_result(value=3.0, reference_min=4.0, reference_max=5.0)
        assert result.deviation_percent() == pytest.approx(-25.0)

    def test_above_max_deviation_is_positive(self):
        result = make_result(value=6.0, reference_min=4.0, reference_max=5.0)
        assert result.deviation_percent() == pytest.approx(20.0)

    def test_missing_value_returns_none(self):
        assert make_result(value=None).deviation_percent() is None


class TestIsCritical:
    def test_small_deviation_is_not_critical(self):
        result = make_result(value=5.6, reference_min=3.9, reference_max=5.5)
        assert result.is_critical() is False

    def test_large_deviation_is_critical(self):
        result = make_result(value=10.0, reference_min=3.9, reference_max=5.5)
        assert result.is_critical() is True

    def test_custom_threshold_is_respected(self):
        result = make_result(value=6.0, reference_min=4.0, reference_max=5.0, critical_threshold_percent=15.0)
        assert result.is_critical() is True


class TestInterpret:
    def test_normal_value(self):
        assert make_result(value=4.5).interpret() == LaboratoryInterpretation.NORMAL

    def test_low_value(self):
        assert make_result(value=3.5).interpret() == LaboratoryInterpretation.LOW

    def test_high_value(self):
        assert make_result(value=6.0).interpret() == LaboratoryInterpretation.HIGH

    def test_critical_low_value(self):
        assert make_result(value=1.0).interpret() == LaboratoryInterpretation.CRITICAL_LOW

    def test_critical_high_value(self):
        assert make_result(value=15.0).interpret() == LaboratoryInterpretation.CRITICAL_HIGH

    def test_unknown_when_value_missing(self):
        assert make_result(value=None).interpret() == LaboratoryInterpretation.UNKNOWN

    def test_unknown_when_reference_range_missing(self):
        result = make_result(reference_min=None, reference_max=None)
        assert result.interpret() == LaboratoryInterpretation.UNKNOWN


class TestTrend:
    def test_insufficient_data_when_no_history(self):
        result = make_result(value=5.0, result_date=date(2026, 1, 10))
        assert result.trend([]) == TrendDirection.INSUFFICIENT_DATA

    def test_insufficient_data_when_history_has_different_test_code(self):
        result = make_result(value=5.0, result_date=date(2026, 1, 10))
        other = make_result(test_code="HBA1C", value=4.0, result_date=date(2026, 1, 1))
        assert result.trend([other]) == TrendDirection.INSUFFICIENT_DATA

    def test_stable_when_change_below_threshold(self):
        result = make_result(value=5.0, result_date=date(2026, 1, 10))
        previous = make_result(value=4.9, result_date=date(2026, 1, 1))
        assert result.trend([previous]) == TrendDirection.STABLE

    def test_up_when_value_increases_significantly(self):
        result = make_result(value=6.0, result_date=date(2026, 1, 10))
        previous = make_result(value=4.0, result_date=date(2026, 1, 1))
        assert result.trend([previous]) == TrendDirection.UP

    def test_down_when_value_decreases_significantly(self):
        result = make_result(value=3.0, result_date=date(2026, 1, 10))
        previous = make_result(value=5.0, result_date=date(2026, 1, 1))
        assert result.trend([previous]) == TrendDirection.DOWN

    def test_compares_against_most_recent_previous_result(self):
        result = make_result(value=6.0, result_date=date(2026, 1, 10))
        older = make_result(value=6.0, result_date=date(2026, 1, 1))
        recent = make_result(value=4.0, result_date=date(2026, 1, 5))
        assert result.trend([older, recent]) == TrendDirection.UP