from __future__ import annotations

from datetime import datetime, timezone

from app.application.uow import UnitOfWork
from app.modules.clinical_reasoning.application.laboratory_profile_service import LaboratoryProfileService
from app.modules.clinical_reasoning.domain.causality import build_causality_assessment
from app.modules.clinical_reasoning.persistence.orm import PatientCausalityAssessmentORM


class ClinicalCausalityService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def assess(self, *, patient_id: str, episode_id: str, result_ids: list[int], persist: bool = True) -> dict:
        profile = LaboratoryProfileService(self.uow).project(
            patient_id=patient_id,
            episode_id=episode_id,
            result_ids=result_ids,
            persist=False,
        )
        assessment = build_causality_assessment(patient_id, episode_id, profile["observations"])

        if persist:
            snapshot = {
                "branches": [branch.__dict__ for branch in assessment.branches],
                "unassigned_fact_ids": assessment.unassigned_fact_ids,
                "devil_review": assessment.devil_review,
            }
            row = self.uow.session.query(PatientCausalityAssessmentORM).filter_by(
                patient_id=patient_id,
                episode_id=episode_id,
            ).one_or_none()
            if row is None:
                row = PatientCausalityAssessmentORM(
                    patient_id=patient_id,
                    episode_id=episode_id,
                    input_result_ids=result_ids,
                    assessment_snapshot=snapshot,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
                self.uow.repo(PatientCausalityAssessmentORM).add(row)
            else:
                row.input_result_ids = result_ids
                row.assessment_snapshot = snapshot
                row.updated_at = datetime.now(timezone.utc)
            self.uow.commit()
        else:
            self.uow.rollback()

        return {
            "patient_id": assessment.patient_id,
            "episode_id": assessment.episode_id,
            "observations": assessment.observations,
            "branches": assessment.branches,
            "unassigned_fact_ids": assessment.unassigned_fact_ids,
            "devil_review": assessment.devil_review,
        }
