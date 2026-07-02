from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.modules.laboratory.application.service import (
    InvalidPatientReferenceError,
    LaboratoryService,
)
from app.modules.laboratory.persistence.orm import LaboratoryResultORM  # noqa: F401 — реєструє repository
from app.modules.laboratory.schemas.laboratory import LaboratoryResultCreate
from app.persistence.base import Base


@pytest.fixture
def in_memory_uow():
    from sqlalchemy import event

    engine = create_engine("sqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def _enable_fk(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)

    from app.application.uow import UnitOfWork

    return UnitOfWork(session_factory=session_factory)


class TestCreateResultInvalidPatientReference:
    def test_raises_invalid_patient_reference_when_profile_does_not_exist(self, in_memory_uow):
        with in_memory_uow as uow:
            service = LaboratoryService(uow)
            data = LaboratoryResultCreate(
                test_name="Glucose",
                test_code="GLU",
                value=5.0,
                reference_min=3.9,
                reference_max=5.5,
                result_date=date(2026, 1, 1),
                patient_profile_id=999,  # не існує
            )

            with pytest.raises(InvalidPatientReferenceError) as exc_info:
                service.create_result(data)

            assert exc_info.value.patient_profile_id == 999

    def test_succeeds_when_patient_profile_id_is_none(self, in_memory_uow):
        with in_memory_uow as uow:
            service = LaboratoryService(uow)
            data = LaboratoryResultCreate(
                test_name="Glucose",
                value=5.0,
                reference_min=3.9,
                reference_max=5.5,
                result_date=date(2026, 1, 1),
                patient_profile_id=None,
            )

            result = service.create_result(data)
            assert result.id is not None
            assert result.patient_profile_id is None