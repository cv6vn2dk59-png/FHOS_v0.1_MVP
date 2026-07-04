from app.modules.laboratory.domain.reference_range import ReferenceRange


def make_range(**overrides) -> ReferenceRange:
    defaults = dict(
        test_code="GLU",
        test_name="Glucose",
        unit="mmol/L",
        reference_min=3.9,
        reference_max=5.5,
    )
    defaults.update(overrides)
    return ReferenceRange(**defaults)


class TestValidation:
    def test_raises_when_min_greater_than_max(self):
        import pytest
        with pytest.raises(ValueError):
            make_range(reference_min=10, reference_max=5)


class TestMatchesTestCodeAndUnit:
    def test_does_not_match_different_test_code(self):
        r = make_range()
        assert r.matches(test_code="TSH", unit="mmol/L") is False

    def test_does_not_match_different_unit(self):
        r = make_range()
        assert r.matches(test_code="GLU", unit="mg/dL") is False

    def test_matches_exact_test_code_and_unit(self):
        r = make_range()
        assert r.matches(test_code="GLU", unit="mmol/L") is True


class TestMatchesSex:
    def test_default_range_matches_any_sex(self):
        r = make_range(sex=None)
        assert r.matches(test_code="GLU", unit="mmol/L", sex="male") is True
        assert r.matches(test_code="GLU", unit="mmol/L", sex="female") is True
        assert r.matches(test_code="GLU", unit="mmol/L", sex=None) is True

    def test_specific_sex_matches_same_sex(self):
        r = make_range(sex="male")
        assert r.matches(test_code="GLU", unit="mmol/L", sex="male") is True

    def test_specific_sex_does_not_match_different_sex(self):
        r = make_range(sex="male")
        assert r.matches(test_code="GLU", unit="mmol/L", sex="female") is False

    def test_specific_sex_does_not_match_unknown_context_sex(self):
        r = make_range(sex="male")
        assert r.matches(test_code="GLU", unit="mmol/L", sex=None) is False


class TestMatchesAge:
    def test_no_age_restriction_matches_any_age(self):
        r = make_range(age_min=None, age_max=None)
        assert r.matches(test_code="GLU", unit="mmol/L", age=5) is True
        assert r.matches(test_code="GLU", unit="mmol/L", age=90) is True
        assert r.matches(test_code="GLU", unit="mmol/L", age=None) is True

    def test_age_restricted_matches_within_bounds(self):
        r = make_range(age_min=18, age_max=65)
        assert r.matches(test_code="GLU", unit="mmol/L", age=30) is True

    def test_age_restricted_does_not_match_below_bounds(self):
        r = make_range(age_min=18, age_max=65)
        assert r.matches(test_code="GLU", unit="mmol/L", age=10) is False

    def test_age_restricted_does_not_match_above_bounds(self):
        r = make_range(age_min=18, age_max=65)
        assert r.matches(test_code="GLU", unit="mmol/L", age=70) is False

    def test_age_restricted_does_not_match_unknown_age(self):
        r = make_range(age_min=18, age_max=65)
        assert r.matches(test_code="GLU", unit="mmol/L", age=None) is False

    def test_open_ended_age_min_only(self):
        r = make_range(age_min=65, age_max=None)
        assert r.matches(test_code="GLU", unit="mmol/L", age=70) is True
        assert r.matches(test_code="GLU", unit="mmol/L", age=50) is False


class TestMatchesLaboratoryAndMethod:
    def test_default_matches_any_laboratory(self):
        r = make_range(laboratory_name=None)
        assert r.matches(test_code="GLU", unit="mmol/L", laboratory_name="Synevo") is True

    def test_specific_laboratory_does_not_match_other_laboratory(self):
        r = make_range(laboratory_name="Synevo")
        assert r.matches(test_code="GLU", unit="mmol/L", laboratory_name="Dila") is False

    def test_specific_method_does_not_match_unknown_context_method(self):
        r = make_range(method="enzymatic")
        assert r.matches(test_code="GLU", unit="mmol/L", method=None) is False


class TestSpecificityScore:
    def test_fully_generic_range_has_zero_score(self):
        r = make_range()
        assert r.specificity_score() == 0
        assert r.is_default() is True

    def test_sex_only_has_score_one(self):
        r = make_range(sex="male")
        assert r.specificity_score() == 1
        assert r.is_default() is False

    def test_sex_and_age_has_score_two(self):
        r = make_range(sex="male", age_min=18, age_max=65)
        assert r.specificity_score() == 2

    def test_all_four_fields_has_score_four(self):
        r = make_range(sex="male", age_min=18, age_max=65, laboratory_name="Synevo", method="enzymatic")
        assert r.specificity_score() == 4