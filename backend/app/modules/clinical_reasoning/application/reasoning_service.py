from __future__ import annotations

from app.application.uow import UnitOfWork
from app.modules.clinical_reasoning.domain.entities import (
    ClinicalHypothesis,
    EvidenceLevel,
    HypothesisOrigin,
    check_hypothesis_expansion,
)
from app.modules.clinical_reasoning.persistence.orm import HealthNodeORM, HealthRelationORM


class ClinicalReasoningService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def expand_hypotheses(
        self,
        symptom_node_id: str,
        user_supplied_title: str | None = None,
        max_results: int = 25,
    ) -> tuple[list[ClinicalHypothesis], dict]:
        node = self.uow.repo(HealthNodeORM).by_external_id(symptom_node_id)
        if node is None:
            raise LookupError(f"HealthNode '{symptom_node_id}' not found")

        relations = self.uow.repo(HealthRelationORM).causes_for(symptom_node_id, limit=max_results)
        hypotheses: list[ClinicalHypothesis] = []

        if user_supplied_title:
            hypotheses.append(
                ClinicalHypothesis(
                    symptom_node_id=symptom_node_id,
                    title=user_supplied_title,
                    mechanism="Причина, запропонована користувачем; потребує незалежної перевірки.",
                    origin=HypothesisOrigin.USER_SUPPLIED,
                    evidence_level=EvidenceLevel.LEVEL_4,
                    verification_questions=["Які факти окремо підтверджують цю версію?"],
                    source_ids=[],
                )
            )

        for relation, cause_node in relations:
            hypotheses.append(
                ClinicalHypothesis(
                    symptom_node_id=symptom_node_id,
                    title=cause_node.label,
                    mechanism=f"{cause_node.label} може пояснювати прояв '{node.label}' згідно зі збереженим ребром графа.",
                    origin=HypothesisOrigin.SYSTEM_GENERATED,
                    evidence_level=EvidenceLevel(relation.evidence_level),
                    body_system=None,
                    etiology_category=cause_node.node_kind,
                    verification_questions=[
                        f"Які клінічні ознаки підтримують або спростовують '{cause_node.label}'?",
                        "Які обстеження потрібні для розмежування цієї гіпотези з іншими?",
                    ],
                    source_ids=[relation.source_citation],
                )
            )

        review = self.devil_review(hypotheses)
        return hypotheses, review

    @staticmethod
    def devil_review(hypotheses: list[ClinicalHypothesis]) -> dict:
        violations = check_hypothesis_expansion(hypotheses)
        if hypotheses and len({h.etiology_category for h in hypotheses if h.etiology_category}) < 2:
            violations.append("Недостатня причинна різноманітність: представлено менше двох етіологічних категорій")
        for hypothesis in hypotheses:
            if hypothesis.origin == HypothesisOrigin.SYSTEM_GENERATED and not hypothesis.verification_questions:
                violations.append(f"'{hypothesis.title}' не має уточнювальних питань")
            if hypothesis.origin == HypothesisOrigin.SYSTEM_GENERATED and not hypothesis.source_ids:
                violations.append(f"'{hypothesis.title}' не має provenance/source_ids")

        return {
            "passed": not violations,
            "violations": violations,
            "questions": [
                "Що в цьому переліку ще не перевірено фактичними даними пацієнта?",
                "Які незалежні альтернативні механізми можуть бути пропущені?",
                "Які системи організму або небезпечні сценарії залишилися поза увагою?",
            ],
        }
