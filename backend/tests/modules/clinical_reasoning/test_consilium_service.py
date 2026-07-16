from datetime import date

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.persistence.model_registry  # noqa: F401
from app.application.uow import UnitOfWork
from app.modules.clinical_reasoning.api.routes import structured_consilium
from app.modules.clinical_reasoning.application.consilium_service import StructuredConsiliumService
from app.modules.clinical_reasoning.schemas.consilium import StructuredConsiliumRequest
from app.modules.clinical_reasoning.persistence.orm import EvidenceSourceORM, HypothesisEvidenceORM
from app.modules.laboratory.persistence.orm import LaboratoryInterpretationORM, LaboratoryResultORM
from app.persistence.base import Base


def make_uow():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return UnitOfWork(sessionmaker(bind=engine, expire_on_commit=False))


def add_result(uow, code, value, interpretation, minimum, maximum):
    return uow.repo(LaboratoryResultORM).add(LaboratoryResultORM(
        test_name=code,
        test_code=code,
        value=value,
        unit="unit",
        reference_min=minimum,
        reference_max=maximum,
        result_date=date(2026, 7, 13),
        interpretation=LaboratoryInterpretationORM(interpretation),
    ))


def test_structured_consilium_preserves_normal_results_and_roles():
    with make_uow() as uow:
        glucose = add_result(uow, "GLUCOSE_FASTING", 7.4, "high", 3.9, 5.5)
        hba1c = add_result(uow, "HBA1C", 6.8, "high", 4.0, 5.6)
        insulin = add_result(uow, "INSULIN_FASTING", 18.0, "normal", 2.6, 24.9)
        creatinine = add_result(uow, "CREATININE", 88.0, "normal", 62.0, 106.0)
        uow.commit()
        result = StructuredConsiliumService(uow).run(
            patient_id="TEST-001", episode_id="ep-1",
            result_ids=[glucose.id, hba1c.id, insulin.id, creatinine.id],
        )
        assert len(result["observations"]) == 4
        roles = [e.role.value for r in result["domain_reports"] for h in r.candidate_hypotheses for e in h.evidence]
        assert "supporting" in roles
        assert "context" in roles
        assert "contradicting" in roles
        assert "diabetes_confirmed" in result["consensus"]["unsafe_conclusions"]


def test_evidence_source_type_is_separate_from_strength_and_idempotent():
    with make_uow() as uow:
        alt = add_result(uow, "ALT", 52.0, "high", 0.0, 41.0)
        uow.commit()
        service = StructuredConsiliumService(uow)
        for _ in range(2):
            service.run(patient_id="TEST-001", episode_id="ep-1", result_ids=[alt.id])
        sources = uow.session.query(EvidenceSourceORM).all()
        assignments = uow.session.query(HypothesisEvidenceORM).all()
        assert len(sources) == 1
        assert sources[0].source_type == "laboratory_result"
        assert sources[0].evidence_strength == "direct_patient_fact"
        assert len(assignments) == 1


def test_structured_consilium_route_returns_serialized_payload():
    with make_uow() as uow:
        glucose = add_result(uow, "GLUCOSE_FASTING", 7.4, "high", 3.9, 5.5)
        insulin = add_result(uow, "INSULIN_FASTING", 18.0, "normal", 2.6, 24.9)
        uow.commit()
        payload = structured_consilium(
            StructuredConsiliumRequest(
                **{
                    "patient_id": "TEST-001",
                    "episode_id": "ep-1",
                    "result_ids": [glucose.id, insulin.id],
                    "persist": True,
                }
            ),
            uow,
        )

        assert payload["patient_id"] == "TEST-001"
        assert payload["domain_reports"][0]["specialty"] == "endocrinology"
        assert payload["domain_reports"][0]["candidate_hypotheses"][0]["evidence"][0]["role"] == "supporting"
        assert payload["devil_review"]["checks"]["diagnosis_auto_confirmation_blocked"] is True


def test_structured_consilium_route_returns_404_for_missing_laboratory_results():
    with make_uow() as uow:
        with pytest.raises(HTTPException) as exc:
            structured_consilium(
                StructuredConsiliumRequest(
                    patient_id="TEST-001",
                    episode_id="ep-1",
                    result_ids=[99999],
                    persist=True,
                ),
                uow,
            )

        assert exc.value.status_code == 404
        assert exc.value.detail == "Laboratory results not found: [99999]"
