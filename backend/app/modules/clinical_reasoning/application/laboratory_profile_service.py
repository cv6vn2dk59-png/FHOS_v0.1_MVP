from __future__ import annotations

from datetime import datetime, timezone

from app.application.uow import UnitOfWork
from app.modules.clinical_reasoning.domain.laboratory_profile import (
    LaboratoryObservationSnapshot,
    build_review_domains,
    classify_observation,
)
from app.modules.clinical_reasoning.persistence.orm import (
    HealthNodeORM,
    LaboratoryGraphObservationORM,
    PatientNodeStateORM,
)
from app.modules.laboratory.persistence.orm import LaboratoryResultORM


class LaboratoryResultsNotFoundError(LookupError):
    pass


class LaboratoryProfileService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    @staticmethod
    def _node_id(result: LaboratoryResultORM) -> str:
        code = (result.test_code or f"RESULT_{result.id}").strip().upper()
        return f"LAB:{code}"

    def project(
        self,
        *,
        patient_id: str,
        episode_id: str,
        result_ids: list[int],
        persist: bool = True,
    ) -> dict:
        rows = self.uow.repo(LaboratoryResultORM).get_by_ids(result_ids)
        found_ids = {row.id for row in rows}
        missing_ids = [result_id for result_id in result_ids if result_id not in found_ids]
        if missing_ids:
            raise LaboratoryResultsNotFoundError(
                f"Laboratory results not found: {missing_ids}"
            )

        observations: list[LaboratoryObservationSnapshot] = []
        for row in rows:
            node_id = self._node_id(row)
            test_code = (row.test_code or f"RESULT_{row.id}").strip().upper()
            node = self.uow.repo(HealthNodeORM).by_external_id(node_id)
            if node is None:
                node = self.uow.repo(HealthNodeORM).add(
                    HealthNodeORM(
                        external_id=node_id,
                        external_source="FHOS_LAB",
                        label=row.test_name,
                        node_kind="Biomarker",
                    )
                )

            observation_class, evidence_role = classify_observation(row.interpretation.value)
            activated_at = datetime.combine(
                row.result_date,
                datetime.min.time(),
                tzinfo=timezone.utc,
            ) if row.result_date is not None else datetime.now(timezone.utc)

            state = self.uow.session.execute(
                __import__("sqlalchemy").select(PatientNodeStateORM).where(
                    PatientNodeStateORM.patient_id == patient_id,
                    PatientNodeStateORM.node_id == node_id,
                    PatientNodeStateORM.episode_id == episode_id,
                )
            ).scalar_one_or_none()
            if state is None:
                state = self.uow.repo(PatientNodeStateORM).add(
                    PatientNodeStateORM(
                        patient_id=patient_id,
                        node_id=node_id,
                        episode_id=episode_id,
                        activated_at=activated_at,
                        family_link_reason=None,
                    )
                )

            provenance = {
                "type": "laboratory_result",
                "laboratory_result_id": row.id,
                "laboratory_name": row.laboratory_name,
                "reference_range_status": row.reference_range_status.value if row.reference_range_status else None,
            }
            graph_observation = self.uow.repo(LaboratoryGraphObservationORM).by_laboratory_result_id(row.id)
            if graph_observation is None:
                graph_observation = LaboratoryGraphObservationORM(
                    laboratory_result_id=row.id,
                    patient_node_state_id=state.id,
                    patient_id=patient_id,
                    episode_id=episode_id,
                    node_id=node_id,
                    test_code=test_code,
                    value=row.value,
                    unit=row.unit,
                    reference_min=row.reference_min,
                    reference_max=row.reference_max,
                    critical_low=row.critical_low,
                    critical_high=row.critical_high,
                    interpretation=row.interpretation.value,
                    observation_class=observation_class.value,
                    evidence_role=evidence_role.value,
                    result_date=row.result_date,
                    provenance=provenance,
                )
                self.uow.repo(LaboratoryGraphObservationORM).add(graph_observation)
            else:
                graph_observation.patient_id = patient_id
                graph_observation.episode_id = episode_id
                graph_observation.patient_node_state_id = state.id
                graph_observation.node_id = node_id
                graph_observation.test_code = test_code
                graph_observation.value = row.value
                graph_observation.unit = row.unit
                graph_observation.reference_min = row.reference_min
                graph_observation.reference_max = row.reference_max
                graph_observation.critical_low = row.critical_low
                graph_observation.critical_high = row.critical_high
                graph_observation.interpretation = row.interpretation.value
                graph_observation.observation_class = observation_class.value
                graph_observation.evidence_role = evidence_role.value
                graph_observation.result_date = row.result_date
                graph_observation.provenance = provenance

            observations.append(
                LaboratoryObservationSnapshot(
                    laboratory_result_id=row.id,
                    patient_id=patient_id,
                    episode_id=episode_id,
                    node_id=node_id,
                    test_code=test_code,
                    test_name=row.test_name,
                    value=row.value,
                    unit=row.unit,
                    reference_min=row.reference_min,
                    reference_max=row.reference_max,
                    critical_low=row.critical_low,
                    critical_high=row.critical_high,
                    interpretation=row.interpretation.value,
                    observation_class=observation_class,
                    evidence_role=evidence_role,
                    result_date=row.result_date.isoformat() if row.result_date else None,
                    provenance=provenance,
                )
            )

        if persist:
            self.uow.commit()
        else:
            self.uow.rollback()

        review_domains = build_review_domains(observations)
        single_measurement_codes = sorted({observation.test_code for observation in observations})
        devil_review = {
            "passed": False,
            "violations": [
                "Лабораторний профіль сам по собі не встановлює діагноз",
                "Для оцінки динаміки потрібні повторні вимірювання в часі",
            ],
            "questions": [
                "Які результати підтверджуються повторними вимірюваннями?",
                "Які нормальні результати обмежують або змінюють кандидатні пояснення?",
                "Якого клінічного контексту, симптомів, ліків або обстежень бракує?",
            ],
            "single_measurement_test_codes": single_measurement_codes,
        }

        return {
            "patient_id": patient_id,
            "episode_id": episode_id,
            "observations": observations,
            "review_domains": review_domains,
            "devil_review": devil_review,
        }
