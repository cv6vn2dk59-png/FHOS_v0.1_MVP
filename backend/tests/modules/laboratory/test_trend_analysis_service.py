from datetime import date

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.application.uow import UnitOfWork
from app.modules.laboratory.application.service import LaboratoryService
from app.modules.laboratory.application.trend_analysis_service import TrendAnalysisService
from app.modules.laboratory.domain.entities import TrendRisk
from app.modules.laboratory.persistence.orm import LaboratoryResultORM  # noqa: F401 — реєструє repository
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


def create_result(service: LaboratoryService, value: float, day: int) -> None:
    service.create_result(
        LaboratoryResultCreate(
            test_name="Glucose",
            test_code="GLU",
            value=value,
            reference_min=3.9,
            reference_max=5.5,
            result_date=date(2026, 1, day),
            patient_profile_id=None,
        )
    )


class TestAssessTrendRiskIntegration:
    def test_increasing_risk_across_stored_results(self, in_memory_uow):
        with in_memory_uow as uow:
            lab_service = LaboratoryService(uow)
            # deviation: (5.8-5.5)/5.5*100≈5.5%; (6.5-5.5)/5.5*100≈18%; (7.5-5.5)/5.5*100≈36%
            create_result(lab_service, value=5.8, day=1)
            create_result(lab_service, value=6.5, day=2)
            create_result(lab_service, value=7.5, day=3)

            trend_service = TrendAnalysisService(uow)
            assessment = trend_service.assess_trend_risk(patient_profile_id=None, test_code="GLU")

            assert assessment.risk == TrendRisk.INCREASING_RISK

    def test_insufficient_data_when_fewer_than_three_results(self, in_memory_uow):
        with in_memory_uow as uow:
            lab_service = LaboratoryService(uow)
            create_result(lab_service, value=5.8, day=1)
            create_result(lab_service, value=6.5, day=2)

            trend_service = TrendAnalysisService(uow)
            assessment = trend_service.assess_trend_risk(patient_profile_id=None, test_code="GLU")

            assert assessment.risk == TrendRisk.INSUFFICIENT_DATA

    def test_ignores_results_of_different_test_code(self, in_memory_uow):
        with in_memory_uow as uow:
            lab_service = LaboratoryService(uow)
            create_result(lab_service, value=5.8, day=1)
            create_result(lab_service, value=6.5, day=2)
            lab_service.create_result(
                LaboratoryResultCreate(
                    test_name="Hemoglobin",
                    test_code="HGB",
                    value=140.0,
                    reference_min=120.0,
                    reference_max=160.0,
                    result_date=date(2026, 1, 3),
                    patient_profile_id=None,
                )
            )

            trend_service = TrendAnalysisService(uow)
            assessment = trend_service.assess_trend_risk(patient_profile_id=None, test_code="GLU")

            assert assessment.risk == TrendRisk.INSUFFICIENT_DATA