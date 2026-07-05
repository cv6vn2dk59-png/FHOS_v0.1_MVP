from datetime import date

import pytest

from app.modules.medications.domain.entities import Medication


def make_medication(**overrides) -> Medication:
    defaults = dict(
        drug_name="Levothyroxine",
        start_date=date(2026, 1, 1),
    )
    defaults.update(overrides)
    return Medication(**defaults)


class TestValidation:
    def test_raises_when_end_date_before_start_date(self):
        with pytest.raises(ValueError):
            make_medication(start_date=date(2026, 6, 1), end_date=date(2026, 1, 1))

    def test_allows_end_date_equal_to_start_date(self):
        med = make_medication(start_date=date(2026, 1, 1), end_date=date(2026, 1, 1))
        assert med.end_date == med.start_date


class TestIsActive:
    def test_active_when_end_date_is_none(self):
        med = make_medication(end_date=None)
        assert med.is_active(as_of=date(2026, 12, 31)) is True

    def test_active_when_as_of_before_end_date(self):
        med = make_medication(start_date=date(2026, 1, 1), end_date=date(2026, 6, 1))
        assert med.is_active(as_of=date(2026, 3, 1)) is True

    def test_active_when_as_of_equals_end_date(self):
        med = make_medication(start_date=date(2026, 1, 1), end_date=date(2026, 6, 1))
        assert med.is_active(as_of=date(2026, 6, 1)) is True

    def test_not_active_when_as_of_after_end_date(self):
        med = make_medication(start_date=date(2026, 1, 1), end_date=date(2026, 6, 1))
        assert med.is_active(as_of=date(2026, 7, 1)) is False


class TestDurationDays:
    def test_duration_with_end_date(self):
        med = make_medication(start_date=date(2026, 1, 1), end_date=date(2026, 1, 11))
        assert med.duration_days() == 10

    def test_duration_without_end_date_uses_as_of(self):
        med = make_medication(start_date=date(2026, 1, 1), end_date=None)
        assert med.duration_days(as_of=date(2026, 1, 21)) == 20

    def test_duration_zero_when_started_today(self):
        med = make_medication(start_date=date(2026, 1, 1), end_date=date(2026, 1, 1))
        assert med.duration_days() == 0