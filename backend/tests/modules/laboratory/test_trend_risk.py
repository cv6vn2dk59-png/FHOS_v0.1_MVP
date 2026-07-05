from datetime import date

from app.modules.laboratory.domain.entities import (
    LaboratoryResult,
    TrendRisk,
    TrendRiskAssessment,
)


def make_result(value: float | None, day: int, ref_min: float = 10.0, ref_max: float = 20.0) -> LaboratoryResult:
    return LaboratoryResult(
        test_name="Test Analyte",
        test_code="TEST",
        patient_profile_id=1,
        value=value,
        reference_min=ref_min,
        reference_max=ref_max,
        result_date=date(2026, 1, day),
    )


class TestInsufficientData:
    def test_fewer_than_three_results(self):
        results = [make_result(15.0, 1), make_result(16.0, 2)]
        assessment = TrendRiskAssessment.assess(results)
        assert assessment.risk == TrendRisk.INSUFFICIENT_DATA

    def test_empty_results(self):
        assessment = TrendRiskAssessment.assess([])
        assert assessment.risk == TrendRisk.INSUFFICIENT_DATA

    def test_missing_value_among_last_three(self):
        results = [make_result(15.0, 1), make_result(None, 2), make_result(25.0, 3)]
        assessment = TrendRiskAssessment.assess(results)
        assert assessment.risk == TrendRisk.INSUFFICIENT_DATA

    def test_missing_reference_range_among_last_three(self):
        results = [
            make_result(15.0, 1),
            LaboratoryResult(test_name="Test Analyte", test_code="TEST", patient_profile_id=1,
                              value=16.0, result_date=date(2026, 1, 2)),
            make_result(17.0, 3),
        ]
        assessment = TrendRiskAssessment.assess(results)
        assert assessment.risk == TrendRisk.INSUFFICIENT_DATA


class TestStable:
    def test_all_within_range_is_stable(self):
        results = [make_result(15.0, 1), make_result(15.5, 2), make_result(14.5, 3)]
        assessment = TrendRiskAssessment.assess(results)
        assert assessment.risk == TrendRisk.STABLE

    def test_small_fluctuation_below_threshold_is_stable(self):
        # reference_max=20, значення трохи вище, зміни < stable_threshold_percent (5%)
        results = [make_result(21.0, 1), make_result(21.2, 2), make_result(21.1, 3)]
        assessment = TrendRiskAssessment.assess(results)
        assert assessment.risk == TrendRisk.STABLE


class TestIncreasingRisk:
    def test_monotonically_worsening_above_upper_bound(self):
        # deviation: (21-20)/20*100=5%, (24-20)/20*100=20%, (28-20)/20*100=40%
        results = [make_result(21.0, 1), make_result(24.0, 2), make_result(28.0, 3)]
        assessment = TrendRiskAssessment.assess(results)
        assert assessment.risk == TrendRisk.INCREASING_RISK
        assert assessment.distances == [5.0, 20.0, 40.0]

    def test_monotonically_worsening_below_lower_bound(self):
        # reference_min=10: (8-10)/10*100=-20% -> abs 20; (6-10)/10*100=-40% -> 40; (4-10)/10*100=-60% -> 60
        results = [make_result(8.0, 1), make_result(6.0, 2), make_result(4.0, 3)]
        assessment = TrendRiskAssessment.assess(results)
        assert assessment.risk == TrendRisk.INCREASING_RISK


class TestDecreasingRisk:
    def test_monotonically_improving_towards_normal(self):
        results = [make_result(28.0, 1), make_result(24.0, 2), make_result(21.0, 3)]
        assessment = TrendRiskAssessment.assess(results)
        assert assessment.risk == TrendRisk.DECREASING_RISK
        assert assessment.distances == [40.0, 20.0, 5.0]


class TestUnclear:
    def test_non_monotonic_change_is_unclear(self):
        # 5% -> 40% -> 10%: різкий стрибок і повернення, не монотонно
        results = [make_result(21.0, 1), make_result(28.0, 2), make_result(22.0, 3)]
        assessment = TrendRiskAssessment.assess(results)
        assert assessment.risk == TrendRisk.UNCLEAR

    def test_uses_only_last_three_of_longer_history(self):
        results = [
            make_result(50.0, 1),  # ігнорується, старіший за останні 3
            make_result(21.0, 2),
            make_result(24.0, 3),
            make_result(28.0, 4),
        ]
        assessment = TrendRiskAssessment.assess(results)
        assert assessment.risk == TrendRisk.INCREASING_RISK
        assert assessment.distances == [5.0, 20.0, 40.0]