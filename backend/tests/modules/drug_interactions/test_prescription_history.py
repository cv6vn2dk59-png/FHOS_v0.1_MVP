from datetime import date

from app.modules.drug_interactions.domain.entities import (
    DrugInteraction,
    InteractionSeverity,
    MedicationRecord,
    find_historical_overlapping_prescriptions,
)

KNOWN = [
    DrugInteraction(
        side_a=["sertraline"],
        side_b=["tranylcypromine"],
        severity=InteractionSeverity.CONTRAINDICATED,
        description="test",
        knowledge_source_id="test_source",
    )
]


def make_record(name, substance, start, end=None):
    return MedicationRecord(drug_name=name, substance=substance, start_date=start, end_date=end)


class TestOverlapDetection:
    def test_overlapping_periods_detected(self):
        records = [
            make_record("Сертралін", "sertraline", date(2026, 1, 1), date(2026, 1, 20)),
            make_record("Транілципромін", "tranylcypromine", date(2026, 1, 10), date(2026, 1, 30)),
        ]
        result = find_historical_overlapping_prescriptions(records, KNOWN)
        assert len(result) == 1
        assert result[0].overlap_start == date(2026, 1, 10)
        assert result[0].overlap_end == date(2026, 1, 20)

    def test_non_overlapping_periods_not_detected(self):
        records = [
            make_record("Сертралін", "sertraline", date(2026, 1, 1), date(2026, 1, 10)),
            make_record("Транілципромін", "tranylcypromine", date(2026, 1, 15), date(2026, 1, 30)),
        ]
        result = find_historical_overlapping_prescriptions(records, KNOWN)
        assert len(result) == 0

    def test_open_ended_end_date_treated_as_ongoing(self):
        records = [
            make_record("Сертралін", "sertraline", date(2026, 1, 1), None),
            make_record("Транілципромін", "tranylcypromine", date(2026, 1, 10), date(2026, 1, 20)),
        ]
        result = find_historical_overlapping_prescriptions(
            records, KNOWN, as_of=date(2026, 2, 1)
        )
        assert len(result) == 1

    def test_no_entry_when_no_known_interaction(self):
        records = [
            make_record("Парацетамол", "paracetamol", date(2026, 1, 1), date(2026, 1, 20)),
            make_record("Ібупрофен", "ibuprofen", date(2026, 1, 10), date(2026, 1, 30)),
        ]
        result = find_historical_overlapping_prescriptions(records, KNOWN)
        assert len(result) == 0

    def test_warning_present_on_every_entry(self):
        records = [
            make_record("Сертралін", "sertraline", date(2026, 1, 1), date(2026, 1, 20)),
            make_record("Транілципромін", "tranylcypromine", date(2026, 1, 10), date(2026, 1, 30)),
        ]
        result = find_historical_overlapping_prescriptions(records, KNOWN)
        assert result[0].warning == "Historical co-prescription is not proof of safety."
