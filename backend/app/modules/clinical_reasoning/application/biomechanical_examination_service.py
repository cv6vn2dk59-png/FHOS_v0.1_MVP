from __future__ import annotations

from dataclasses import asdict

from app.modules.clinical_reasoning.domain.biomechanical_examination import (
    BiomechanicalExaminationEngine,
    ExaminationFinding,
    ExaminationFindingKind,
    FindingResult,
)
from app.modules.clinical_reasoning.domain.causality import ContextConstraint, ProvenanceReference
from app.modules.clinical_reasoning.domain.hypothesis_expansion import BranchStatus, HypothesisBranch


class BiomechanicalExaminationService:
    def __init__(self) -> None:
        self.engine = BiomechanicalExaminationEngine()

    def evaluate(self, case_id: str, branches: list[dict], findings: list[dict]) -> dict:
        domain_branches = [
            HypothesisBranch(
                id=item["id"], case_id=item["case_id"], title=item["title"],
                description=item["description"], root_trigger_ids=item.get("root_trigger_ids", []),
                causal_domain=item["causal_domain"], branch_type=item["branch_type"],
                node_ids=item.get("node_ids", []), edge_ids=item.get("edge_ids", []),
                supporting_fact_ids=item.get("supporting_fact_ids", []),
                contradicting_fact_ids=item.get("contradicting_fact_ids", []),
                neutral_fact_ids=item.get("neutral_fact_ids", []),
                missing_evidence_ids=item.get("missing_evidence_ids", []),
                evidence_strength=item["evidence_strength"], confidence=item["confidence"],
                status=BranchStatus(item["status"]),
                provenance=[ProvenanceReference(**value) for value in item["provenance"]],
                context_constraints=[ContextConstraint(**value) for value in item.get("context_constraints", [])],
                safety_critical=item.get("safety_critical", False),
            ) for item in branches
        ]
        domain_findings = [
            ExaminationFinding(
                id=item["id"], kind=ExaminationFindingKind(item["kind"]), code=item["code"],
                result=FindingResult(item["result"]), value=item.get("value"),
                body_region=item.get("body_region"), laterality=item.get("laterality"),
                provenance=[ProvenanceReference(**value) for value in item["provenance"]],
                context_constraints=[ContextConstraint(**value) for value in item.get("context_constraints", [])],
            ) for item in findings
        ]
        return asdict(self.engine.evaluate(case_id, domain_branches, domain_findings))
