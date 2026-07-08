from datetime import date

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.application.uow import UnitOfWork
from app.modules.diseases.application.service import (
    DiseaseService,
    InvalidPatientReferenceError,
)
from app.modules.diseases.persistence.orm import DiseaseORM  # noqa: F401 — реєструє repository
import app.modules.diseases.persistence.repository  # noqa: F401
import app.modules.profile.persistence.orm  # noqa: F401
from app.modules.diseases.schemas.diseases import DiseaseCreate
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


class TestCreateDiseaseInvalidPatientReference:
    def test_raises_invalid_patient_reference_when_profile_does_not_exist(self, in_memory_uow):
        with in_memory_uow as uow:
            service = DiseaseService(uow)
            data = DiseaseCreate(
                diagnosis_name="Цукровий діабет 2 типу",
                onset_date=date(2026, 1, 1),
                patient_profile_id=999,  # не існує
            )

            with pytest.raises(InvalidPatientReferenceError) as exc_info:
                service.create_disease(data)

            assert exc_info.value.patient_profile_id == 999

    def test_succeeds_when_patient_profile_id_is_none(self, in_memory_uow):
        with in_memory_uow as uow:
            service = DiseaseService(uow)
            data = DiseaseCreate(
                diagnosis_name="Цукровий діабет 2 типу",
                onset_date=date(2026, 1, 1),
                patient_profile_id=None,
            )

            result = service.create_disease(data)
            assert result.id is not None
            assert result.patient_profile_id is None


class TestListDiseasesForPatient:
    def test_lists_diseases_for_patient(self, in_memory_uow):
        with in_memory_uow as uow:
            service = DiseaseService(uow)
            service.create_disease(DiseaseCreate(
                diagnosis_name="Гіпертонічна хвороба",
                onset_date=date(2026, 1, 1),
                patient_profile_id=None,
            ))
            service.create_disease(DiseaseCreate(
                diagnosis_name="Цукровий діабет 2 типу",
                onset_date=date(2026, 2, 1),
                patient_profile_id=None,
            ))

            diseases = service.list_diseases_for_patient(patient_profile_id=None)
            assert len(diseases) == 2

    def test_returns_empty_list_when_no_diseases(self, in_memory_uow):
        with in_memory_uow as uow:
            service = DiseaseService(uow)
            diseases = service.list_diseases_for_patient(patient_profile_id=None)
            assert diseases == []
