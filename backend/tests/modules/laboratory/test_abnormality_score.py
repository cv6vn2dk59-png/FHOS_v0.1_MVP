from datetime import date

import pytest

from app.modules.laboratory.domain.entities import LaboratoryResult


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


class TestAbnormalityScoreMissingData:
    def test_none_when_value_missing(self):
        assert make_result(value=None).abnormality_score() is None

    def test_none_when_reference_range_missing(self):
        result = make_result(reference_min=None, reference_max=None)
        assert result.abnormality_score() is None


class TestAbnormalityScoreNormal:
    def test_zero_when_within_range(self):
        assert make_result(value=4.5).abnormality_score() == 0.0

    def test_zero_at_exact_boundary_min(self):
        result = make_result(value=3.9, reference_min=3.9, reference_max=5.5)
        assert result.abnormality_score() == 0.0


class TestAbnormalityScoreBoundaries:
    def test_exactly_10_percent_is_mild(self):
        result = make_result(value=5.5, reference_min=4.0, reference_max=5.0)
        assert result.deviation_percent() == pytest.approx(10.0)
        assert result.abnormality_score() == 0.25

    def test_just_above_10_percent_is_moderate(self):
        result = make_result(value=5.51, reference_min=4.0, reference_max=5.0)
        assert result.deviation_percent() > 10.0
        assert result.abnormality_score() == 0.5

    def test_exactly_30_percent_is_moderate(self):
        result = make_result(value=6.5, reference_min=4.0, reference_max=5.0)
        assert result.deviation_percent() == pytest.approx(30.0)
        assert result.abnormality_score() == 0.5

    def test_just_above_30_percent_is_significant(self):
        result = make_result(value=6.51, reference_min=4.0, reference_max=5.0)
        assert result.deviation_percent() > 30.0
        assert result.abnormality_score() == 0.75

    def test_exactly_50_percent_is_significant(self):
        result = make_result(value=7.5, reference_min=4.0, reference_max=5.0)
        assert result.deviation_percent() == pytest.approx(50.0)
        assert result.abnormality_score() == 0.75

    def test_just_above_50_percent_is_critical(self):
        result = make_result(value=7.51, reference_min=4.0, reference_max=5.0)
        assert result.deviation_percent() > 50.0
        assert result.abnormality_score() == 1.0

    def test_negative_deviation_uses_absolute_value(self):
        result = make_result(value=2.5, reference_min=4.0, reference_max=5.0)
        assert result.deviation_percent() == pytest.approx(-37.5)
        assert result.abnormality_score() == 0.75


class TestAbnormalityScoreNegativeBoundaries:
    def test_negative_10_percent_is_mild(self):
        result = make_result(value=3.6, reference_min=4.0, reference_max=5.0)
        assert result.deviation_percent() == pytest.approx(-10.0)
        assert result.abnormality_score() == 0.25

    def test_negative_60_percent_is_critical(self):
        result = make_result(value=1.6, reference_min=4.0, reference_max=5.0)
        assert result.deviation_percent() == pytest.approx(-60.0)
        assert result.abnormality_score() == 1.0


class TestRiskScoreAlias:
    def test_risk_score_equals_abnormality_score_normal(self):
        result = make_result(value=4.5)
        assert result.risk_score() == result.abnormality_score() == 0.0

    def test_risk_score_equals_abnormality_score_critical(self):
        result = make_result(value=15.0, reference_min=3.9, reference_max=5.5)
        assert result.risk_score() == result.abnormality_score() == 1.0

    def test_risk_score_none_when_data_missing(self):
        result = make_result(value=None)
        assert result.risk_score() is None