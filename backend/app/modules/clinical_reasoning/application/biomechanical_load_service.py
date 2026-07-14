from __future__ import annotations
from dataclasses import asdict
from app.modules.clinical_reasoning.domain.biomechanical_load import (
    BiomechanicalLoadEngine, LoadExposure, LoadExposureKind, RecoveryCapacity, LoadResponseObservation,
)
from app.modules.clinical_reasoning.domain.causality import ContextConstraint, ProvenanceReference
from app.modules.clinical_reasoning.domain.hypothesis_expansion import BranchStatus, HypothesisBranch

class BiomechanicalLoadService:
    def __init__(self) -> None:
        self.engine = BiomechanicalLoadEngine()

    def evaluate(self, case_id: str, branches: list[dict], exposures: list[dict], recovery: dict | None, responses: list[dict]) -> dict:
        def prov(items): return [ProvenanceReference(**item) for item in items]
        def ctx(items): return [ContextConstraint(**item) for item in items]
        domain_branches = [HypothesisBranch(
            id=item["id"], case_id=item["case_id"], title=item["title"], description=item["description"],
            root_trigger_ids=item.get("root_trigger_ids", []), causal_domain=item["causal_domain"], branch_type=item["branch_type"],
            node_ids=item.get("node_ids", []), edge_ids=item.get("edge_ids", []), supporting_fact_ids=item.get("supporting_fact_ids", []),
            contradicting_fact_ids=item.get("contradicting_fact_ids", []), neutral_fact_ids=item.get("neutral_fact_ids", []),
            missing_evidence_ids=item.get("missing_evidence_ids", []), evidence_strength=item["evidence_strength"], confidence=item["confidence"],
            status=BranchStatus(item["status"]), provenance=prov(item["provenance"]), context_constraints=ctx(item.get("context_constraints", [])),
            safety_critical=item.get("safety_critical", False),
        ) for item in branches]
        domain_exposures = [LoadExposure(
            id=item["id"], kind=LoadExposureKind(item["kind"]), code=item["code"], magnitude=item.get("magnitude"),
            duration_minutes=item.get("duration_minutes"), frequency_per_week=item.get("frequency_per_week"),
            occurred_at=item.get("occurred_at"), body_region=item.get("body_region"), provenance=prov(item["provenance"]),
            context_constraints=ctx(item.get("context_constraints", [])),
        ) for item in exposures]
        domain_recovery = None if recovery is None else RecoveryCapacity(
            id=recovery["id"], sleep_quality=recovery.get("sleep_quality"), recovery_hours=recovery.get("recovery_hours"),
            baseline_capacity=recovery.get("baseline_capacity"), current_capacity=recovery.get("current_capacity"),
            limiting_factors=tuple(recovery.get("limiting_factors", [])), provenance=prov(recovery["provenance"]),
            context_constraints=ctx(recovery.get("context_constraints", [])),
        )
        domain_responses = [LoadResponseObservation(
            id=item["id"], exposure_id=item["exposure_id"], symptom_change=item.get("symptom_change"),
            onset_delay_hours=item.get("onset_delay_hours"), recovery_time_hours=item.get("recovery_time_hours"),
            functional_change=item.get("functional_change"), repeated_pattern=item.get("repeated_pattern"),
            provenance=prov(item["provenance"]), context_constraints=ctx(item.get("context_constraints", [])),
        ) for item in responses]
        return asdict(self.engine.evaluate(case_id, domain_branches, domain_exposures, domain_recovery, domain_responses))
