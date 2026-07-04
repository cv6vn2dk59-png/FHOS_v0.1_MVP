from datetime import date

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.application.uow import UnitOfWork
from app.modules.laboratory.application.service import LaboratoryService
from app.modules.laboratory.domain.entities import ReferenceRangeStatus
from app.modules.laboratory.persistence.orm import LaboratoryResultORM  # noqa: F401
from app.modules.laboratory.persistence.reference_range_orm import ReferenceRangeORM
import app.modules.laboratory.persistence.reference_range_repository  # noqa: F401
from app.modules.laboratory.schemas.laboratory import LaboratoryResultCreate
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


def seed_reference_range(session, **overrides):
    defaults = dict(
        test_code="GLU",
        test_name="Glucose",
        unit="mmol/L",
        reference_min=3.9,
        reference_max=5.5,
    )
    defaults.update(overrides)
    row = ReferenceRangeORM(**defaults)
    session.add(row)
    session.commit()
    return row


class TestManualOverride:
    def test_manual_reference_range_skips_resolver(self, in_memory_uow):
        with in_memory_uow as uow:
            service = LaboratoryService(uow)
            data = LaboratoryResultCreate(
                test_name="Glucose",
                test_code="GLU",
                unit="mmol/L",
                value=6.0,
                reference_min=3.0,
                reference_max=5.0,
                result_date=date(2026, 1, 1),
            )
            result = service.create_result(data)
            assert result.reference_range_status == ReferenceRangeStatus.MANUAL
            assert result.reference_min == 3.0
            assert result.reference_max == 5.0


class TestAutoResolution:
    def test_resolves_default_range_when_not_provided(self, in_memory_uow):
        with in_memory_uow as uow:
            seed_reference_range(uow.session)
            service = LaboratoryService(uow)
            data = LaboratoryResultCreate(
                test_name="Glucose",
                test_code="GLU",
                unit="mmol/L",
                value=6.0,
                result_date=date(2026, 1, 1),
            )
            result = service.create_result(data)
            assert result.reference_range_status == ReferenceRangeStatus.RESOLVED
            assert result.reference_min == 3.9
            assert result.reference_max == 5.5

    def test_resolves_sex_specific_range_over_default(self, in_memory_uow):
        with in_memory_uow as uow:
            seed_reference_range(uow.session, sex=None, reference_min=3.3, reference_max=5.8)
            seed_reference_range(uow.session, sex="female", reference_min=3.5, reference_max=5.5)

            service = LaboratoryService(uow)
            data = LaboratoryResultCreate(
                test_name="Glucose",
                test_code="GLU",
                unit="mmol/L",
                value=6.0,
                result_date=date(2026, 1, 1),
            )
            result = service.create_result(data, sex="female")
            assert result.reference_range_status == ReferenceRangeStatus.RESOLVED
            assert result.reference_min == 3.5


class TestNotFound:
    def test_not_found_when_no_matching_range_exists(self, in_memory_uow):
        with in_memory_uow as uow:
            service = LaboratoryService(uow)
            data = LaboratoryResultCreate(
                test_name="Glucose",
                test_code="GLU",
                unit="mmol/L",
                value=6.0,
                result_date=date(2026, 1, 1),
            )
            result = service.create_result(data)
            assert result.reference_range_status == ReferenceRangeStatus.NOT_FOUND
            assert result.reference_min is None
            assert result.reference_max is None

    def test_not_found_when_test_code_missing(self, in_memory_uow):
        with in_memory_uow as uow:
            seed_reference_range(uow.session)
            service = LaboratoryService(uow)
            data = LaboratoryResultCreate(
                test_name="Glucose",
                unit="mmol/L",
                value=6.0,
                result_date=date(2026, 1, 1),
            )
            result = service.create_result(data)
            assert result.reference_range_status == ReferenceRangeStatus.NOT_FOUND