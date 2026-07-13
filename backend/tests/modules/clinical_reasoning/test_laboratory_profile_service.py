from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.persistence.model_registry  # noqa: F401
from app.application.uow import UnitOfWork
from app.modules.clinical_reasoning.application.laboratory_profile_service import LaboratoryProfileService
from app.modules.clinical_reasoning.persistence.orm import LaboratoryGraphObservationORM, PatientNodeStateORM
from app.modules.laboratory.persistence.orm import LaboratoryInterpretationORM, LaboratoryResultORM
from app.persistence.base import Base


def make_uow():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return UnitOfWork(sessionmaker(bind=engine, expire_on_commit=False))


def add_result(uow, code, name, value, interpretation, minimum, maximum):
    return uow.repo(LaboratoryResultORM).add(
        LaboratoryResultORM(
            test_name=name,
            test_code=code,
            value=value,
            unit="unit",
            reference_min=minimum,
            reference_max=maximum,
            result_date=date(2026, 7, 13),
            interpretation=LaboratoryInterpretationORM(interpretation),
        )
    )


def test_full_profile_keeps_normal_and_abnormal_results():
    with make_uow() as uow:
        glucose = add_result(uow, "GLUCOSE_FASTING", "Glucose", 7.4, "high", 3.9, 5.5)
        insulin = add_result(uow, "INSULIN_FASTING", "Insulin", 18.0, "normal", 2.6, 24.9)
        creatinine = add_result(uow, "CREATININE", "Creatinine", 88.0, "normal", 62.0, 106.0)
        uow.commit()

        result = LaboratoryProfileService(uow).project(
            patient_id="TEST-001",
            episode_id="episode-lab-1",
            result_ids=[glucose.id, insulin.id, creatinine.id],
        )

        assert len(result["observations"]) == 3
        by_code = {item.test_code: item for item in result["observations"]}
        assert by_code["GLUCOSE_FASTING"].evidence_role.value == "signal"
        assert by_code["INSULIN_FASTING"].evidence_role.value == "context"
        assert by_code["CREATININE"].evidence_role.value == "context"


def test_projection_persists_provenance_and_is_idempotent():
    with make_uow() as uow:
        alt = add_result(uow, "ALT", "ALT", 52.0, "high", 0.0, 41.0)
        uow.commit()
        service = LaboratoryProfileService(uow)

        for _ in range(2):
            service.project(
                patient_id="TEST-001",
                episode_id="episode-lab-1",
                result_ids=[alt.id],
            )

        observations = uow.repo(LaboratoryGraphObservationORM).for_episode("TEST-001", "episode-lab-1")
        assert len(observations) == 1
        assert observations[0].provenance["laboratory_result_id"] == alt.id
        assert len(uow.repo(PatientNodeStateORM).for_patients(["TEST-001"])) == 1


def test_review_domains_use_all_relevant_results():
    with make_uow() as uow:
        glucose = add_result(uow, "GLUCOSE_FASTING", "Glucose", 7.4, "high", 3.9, 5.5)
        insulin = add_result(uow, "INSULIN_FASTING", "Insulin", 18.0, "normal", 2.6, 24.9)
        uow.commit()
        result = LaboratoryProfileService(uow).project(
            patient_id="TEST-001",
            episode_id="episode-lab-1",
            result_ids=[glucose.id, insulin.id],
        )
        domain = next(item for item in result["review_domains"] if item.code == "glycemic_regulation")
        assert domain.status == "attention"
        assert domain.signal_result_ids == [glucose.id]
        assert domain.context_result_ids == [insulin.id]
        assert set(domain.evidence_result_ids) == {glucose.id, insulin.id}
