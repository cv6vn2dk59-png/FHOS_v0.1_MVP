from datetime import date

import pytest

from app.modules.diseases.domain.entities import Disease


def make_disease(**overrides) -> Disease:
    defaults = dict(
        diagnosis_name="Гіпертонічна хвороба",
        onset_date=date(2026, 1, 1),
    )
    defaults.update(overrides)
    return Disease(**defaults)


class TestValidation:
    def test_raises_when_resolved_date_before_onset_date(self):
        with pytest.raises(ValueError):
            make_disease(onset_date=date(2026, 6, 1), resolved_date=date(2026, 1, 1))

    def test_allows_resolved_date_equal_to_onset_date(self):
        disease = make_disease(onset_date=date(2026, 1, 1), resolved_date=date(2026, 1, 1))
        assert disease.resolved_date == disease.onset_date


class TestIsActive:
    def test_active_when_resolved_date_is_none(self):
        disease = make_disease(resolved_date=None)
        assert disease.is_active(as_of=date(2026, 12, 31)) is True

    def test_active_when_as_of_before_resolved_date(self):
        disease = make_disease(onset_date=date(2026, 1, 1), resolved_date=date(2026, 6, 1))
        assert disease.is_active(as_of=date(2026, 3, 1)) is True

    def test_active_when_as_of_equals_resolved_date(self):
        disease = make_disease(onset_date=date(2026, 1, 1), resolved_date=date(2026, 6, 1))
        assert disease.is_active(as_of=date(2026, 6, 1)) is True

    def test_not_active_when_as_of_after_resolved_date(self):
        disease = make_disease(onset_date=date(2026, 1, 1), resolved_date=date(2026, 6, 1))
        assert disease.is_active(as_of=date(2026, 7, 1)) is False


class TestDurationDays:
    def test_duration_with_resolved_date(self):
        disease = make_disease(onset_date=date(2026, 1, 1), resolved_date=date(2026, 1, 11))
        assert disease.duration_days() == 10

    def test_duration_without_resolved_date_uses_as_of(self):
        disease = make_disease(onset_date=date(2026, 1, 1), resolved_date=None)
        assert disease.duration_days(as_of=date(2026, 1, 21)) == 20

    def test_duration_zero_when_started_today(self):
        disease = make_disease(onset_date=date(2026, 1, 1), resolved_date=date(2026, 1, 1))
        assert disease.duration_days() == 0


class TestOptionalFields:
    def test_icd_code_defaults_to_none(self):
        disease = make_disease()
        assert disease.icd_code is None

    def test_icd_code_can_be_set(self):
        disease = make_disease(icd_code="I10")
        assert disease.icd_code == "I10"
