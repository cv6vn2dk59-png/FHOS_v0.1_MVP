from datetime import date

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.application.uow import UnitOfWork
from app.modules.drug_interactions.application.service import DrugInteractionService
import app.modules.drug_interactions.persistence.orm  # noqa: F401
import app.modules.drug_interactions.persistence.repository  # noqa: F401
import app.modules.profile.persistence.orm  # noqa: F401
from app.modules.medications.application.service import MedicationService
import app.modules.medications.persistence.orm  # noqa: F401
import app.modules.medications.persistence.repository  # noqa: F401
from app.modules.medications.schemas.medications import MedicationCreate
from app.persistence.base import Base


@pytest.fixture
def in_memory_uow():
    engine = create_engine("sqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def _enable_fk(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    return UnitOfWork(session_factory=session_factory)


def create_medication(service, drug_name, start_day, end_day=None):
    service.create_medication(
        MedicationCreate(
            drug_name=drug_name,
            start_date=date(2026, 1, start_day),
            end_date=date(2026, 1, end_day) if end_day else None,
            patient_profile_id=None,
        )
    )


class TestFindPrescriptionHistory:
    def test_finds_overlapping_historical_prescriptions(self, in_memory_uow):
        with in_memory_uow as uow:
            med_service = MedicationService(uow)
            create_medication(med_service, "сертралін", start_day=1, end_day=20)
            create_medication(med_service, "транілципромін", start_day=10, end_day=30)

            di_service = DrugInteractionService(uow)
            result = di_service.find_prescription_history(patient_profile_id=None)

            assert len(result) == 1
            assert result[0].overlap_start == date(2026, 1, 10)
            assert result[0].warning == "Historical co-prescription is not proof of safety."

    def test_finds_nothing_when_periods_do_not_overlap(self, in_memory_uow):
        with in_memory_uow as uow:
            med_service = MedicationService(uow)
            create_medication(med_service, "сертралін", start_day=1, end_day=5)
            create_medication(med_service, "транілципромін", start_day=10, end_day=20)

            di_service = DrugInteractionService(uow)
            result = di_service.find_prescription_history(patient_profile_id=None)

            assert len(result) == 0

    def test_includes_finished_medications_not_only_active(self, in_memory_uow):
        with in_memory_uow as uow:
            med_service = MedicationService(uow)
            # Обидва препарати вже завершені -- не в check_active_medications,
            # але МАЮТЬ бути в prescription_history (вся історія, не тільки активні).
            create_medication(med_service, "сертралін", start_day=1, end_day=20)
            create_medication(med_service, "транілципромін", start_day=10, end_day=15)

            di_service = DrugInteractionService(uow)
            result = di_service.find_prescription_history(patient_profile_id=None)

            assert len(result) == 1
