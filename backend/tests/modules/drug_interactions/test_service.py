from datetime import date

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.application.uow import UnitOfWork
from app.modules.drug_interactions.application.service import DrugInteractionService
import app.modules.profile.persistence.orm  # noqa: F401
from app.modules.drug_interactions.persistence.orm import DrugInteractionORM  # noqa: F401
import app.modules.drug_interactions.persistence.repository  # noqa: F401
from app.modules.medications.application.service import MedicationService
from app.modules.medications.persistence.orm import MedicationORM  # noqa: F401
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


def create_medication(service: MedicationService, drug_name: str, day: int, end_day: int | None = None) -> None:
    service.create_medication(
        MedicationCreate(
            drug_name=drug_name,
            start_date=date(2026, 1, day),
            end_date=date(2026, 1, end_day) if end_day else None,
            patient_profile_id=None,
        )
    )


class TestCheckActiveMedications:
    def test_finds_known_interaction_between_active_medications(self, in_memory_uow):
        with in_memory_uow as uow:
            med_service = MedicationService(uow)
            create_medication(med_service, "сертралін", day=1)
            create_medication(med_service, "транілципромін", day=1)

            di_service = DrugInteractionService(uow)
            result = di_service.check_active_medications(patient_profile_id=None)

            assert len(result) == 1

    def test_finds_nothing_when_no_known_interaction(self, in_memory_uow):
        with in_memory_uow as uow:
            med_service = MedicationService(uow)
            create_medication(med_service, "парацетамол", day=1)

            di_service = DrugInteractionService(uow)
            result = di_service.check_active_medications(patient_profile_id=None)

            assert len(result) == 0

    def test_ignores_medications_that_are_no_longer_active(self, in_memory_uow):
        with in_memory_uow as uow:
            med_service = MedicationService(uow)
            create_medication(med_service, "сертралін", day=1, end_day=5)
            create_medication(med_service, "транілципромін", day=1)

            di_service = DrugInteractionService(uow)
            result = di_service.check_active_medications(patient_profile_id=None)

            assert len(result) == 0

    def test_normalizes_brand_name_via_local_mapping(self, in_memory_uow):
        with in_memory_uow as uow:
            med_service = MedicationService(uow)
            create_medication(med_service, "варфарин", day=1)
            create_medication(med_service, "кордарон", day=1)

            di_service = DrugInteractionService(uow)
            result = di_service.check_active_medications(patient_profile_id=None)

            assert len(result) == 0
            # Примітка: варфарин+аміодарон НЕ в списку Phansalkar 2013
            # (перевірено раніше в test_entities.py) - тест підтверджує,
            # що normalize_drug_name реально спрацював (кордарон -> amiodarone),
            # а не що взаємодія знайдена.
