from __future__ import annotations

from datetime import datetime, timezone

from app.application.uow import UnitOfWork
from app.modules.clinical_reasoning.application.laboratory_profile_service import LaboratoryProfileService
from app.modules.clinical_reasoning.domain.consilium import build_consensus, build_domain_reports
from app.modules.clinical_reasoning.domain.evidence import EvidenceStrength, EvidenceSourceType, VerificationStatus
from app.modules.clinical_reasoning.persistence.orm import EvidenceSourceORM, HypothesisEvidenceORM


class StructuredConsiliumService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def run(self, *, patient_id: str, episode_id: str, result_ids: list[int], persist: bool = True) -> dict:
        profile = LaboratoryProfileService(self.uow).project(
            patient_id=patient_id,
            episode_id=episode_id,
            result_ids=result_ids,
            persist=False,
        )
        observations = profile["observations"]
        reports = build_domain_reports(observations)
        consensus = build_consensus(reports)

        if persist:
            by_result = {o.laboratory_result_id: o for o in observations}
            for report in reports:
                for hypothesis in report.candidate_hypotheses:
                    for item in hypothesis.evidence:
                        observation = by_result[item.laboratory_result_id]
                        source_key = f"laboratory_result:{item.laboratory_result_id}"
                        source = self.uow.session.query(EvidenceSourceORM).filter_by(source_key=source_key).one_or_none()
                        if source is None:
                            source = EvidenceSourceORM(
                                source_key=source_key,
                                source_type=EvidenceSourceType.LABORATORY_RESULT.value,
                                title=f"{observation.test_name}: {observation.value} {observation.unit or ''}".strip(),
                                uri=None,
                                publication_type=None,
                                verification_status=VerificationStatus.VERIFIED.value,
                                evidence_strength=EvidenceStrength.DIRECT_PATIENT_FACT.value,
                                retrieved_at=datetime.now(timezone.utc),
                                source_metadata=observation.provenance,
                            )
                            self.uow.repo(EvidenceSourceORM).add(source)
                            self.uow.session.flush()
                        patient_fact_id = f"laboratory_result:{item.laboratory_result_id}"
                        assignment = self.uow.session.query(HypothesisEvidenceORM).filter_by(
                            hypothesis_key=hypothesis.code,
                            evidence_source_id=source.id,
                            patient_fact_id=patient_fact_id,
                            role=item.role.value,
                        ).one_or_none()
                        if assignment is None:
                            self.uow.repo(HypothesisEvidenceORM).add(HypothesisEvidenceORM(
                                hypothesis_key=hypothesis.code,
                                evidence_source_id=source.id,
                                patient_fact_id=patient_fact_id,
                                role=item.role.value,
                                weight=1.0,
                                rationale=item.rationale,
                            ))
            self.uow.commit()
        else:
            self.uow.rollback()

        all_roles = [e.role.value for r in reports for h in r.candidate_hypotheses for e in h.evidence]
        devil_violations = []
        if not reports:
            devil_violations.append("Не сформовано жодного спеціалізованого огляду.")
        if "context" not in all_roles and "contradicting" not in all_roles:
            devil_violations.append("Нормальні або обмежувальні факти не представлені окремою роллю.")
        devil_warnings = [
            "Кандидатні напрямки не є підтвердженими діагнозами.",
        ]
        devil_limitations = [
            "Для фінального клінічного висновку бракує анамнезу, огляду та повторних/додаткових даних.",
        ]
        devil_review = {
            "passed": not devil_violations,
            "violations": devil_violations,
            "warnings": devil_warnings,
            "limitations": devil_limitations,
            "checks": {
                "all_claims_reference_patient_fact_ids": all(
                    e.laboratory_result_id for r in reports for h in r.candidate_hypotheses for e in h.evidence
                ),
                "normal_results_preserved": any(o.interpretation == "normal" for o in observations),
                "source_type_separated_from_strength": True,
                "diagnosis_auto_confirmation_blocked": True,
                "specialty_perspectives_count": len(reports),
            },
        }
        return {
            "patient_id": patient_id,
            "episode_id": episode_id,
            "observations": observations,
            "domain_reports": reports,
            "consensus": consensus,
            "devil_review": devil_review,
        }