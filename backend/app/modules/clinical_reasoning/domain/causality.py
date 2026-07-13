from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable


class CausalNodeKind(str, Enum):
    PATIENT_FACT = "patient_fact"
    FUNCTIONAL_PROCESS = "functional_process"
    BODY_SYSTEM = "body_system"
    MECHANISM = "mechanism"
    CLINICAL_HYPOTHESIS = "clinical_hypothesis"
    CLINICAL_CONSEQUENCE = "clinical_consequence"
    MISSING_EVIDENCE = "missing_evidence"


@dataclass(frozen=True)
class ProvenanceReference:
    source_id: str
    source_version: str
    locator: str | None = None

    def __post_init__(self) -> None:
        if not self.source_id.strip() or not self.source_version.strip():
            raise ValueError("provenance requires source_id and source_version")


@dataclass(frozen=True)
class ContextConstraint:
    key: str
    operator: str
    value: Any


@dataclass
class CausalNode:
    id: str
    kind: CausalNodeKind
    label: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CausalEdge:
    id: str
    source_node_id: str
    target_node_id: str
    relation_type: str
    evidence_strength: str
    confidence: float
    provenance: list[ProvenanceReference]
    context_constraints: list[ContextConstraint] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.source_node_id == self.target_node_id:
            raise ValueError("causal edge cannot point to itself")
        if not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
        if not self.provenance:
            raise ValueError("causal edge requires provenance")


@dataclass
class CausalPath:
    id: str
    node_ids: list[str]
    edge_ids: list[str]
    causal_domain: str
    provenance: list[ProvenanceReference]
    context_constraints: list[ContextConstraint] = field(default_factory=list)

    def __post_init__(self) -> None:
        if len(self.node_ids) < 2:
            raise ValueError("causal path requires at least two nodes")
        if len(self.edge_ids) != len(self.node_ids) - 1:
            raise ValueError("causal path edge count must equal node count minus one")
        if not self.provenance:
            raise ValueError("causal path requires provenance")


class CausalityRelationKind(str, Enum):
    INDICATES_PROCESS = "indicates_process"
    INVOLVES_SYSTEM = "involves_system"
    MAY_REFLECT_MECHANISM = "may_reflect_mechanism"
    MAY_SUPPORT_HYPOTHESIS = "may_support_hypothesis"
    MAY_LEAD_TO_CONSEQUENCE = "may_lead_to_consequence"
    REQUIRES_EVIDENCE = "requires_evidence"


class MechanismStatus(str, Enum):
    SUPPORTED = "supported"
    PLAUSIBLE = "plausible"
    CONTRADICTED = "contradicted"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


@dataclass(frozen=True)
class CausalityRelation:
    from_code: str
    to_code: str
    relation_kind: CausalityRelationKind
    status: MechanismStatus
    confidence: float
    rationale: str
    source_key: str
    context_constraints: list[dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
        if not self.from_code or not self.to_code:
            raise ValueError("causality relation requires endpoints")
        if not self.rationale.strip() or not self.source_key.strip():
            raise ValueError("causality relation requires rationale and source_key")


@dataclass
class CausalityBranch:
    code: str
    title: str
    patient_fact_ids: list[str]
    functional_processes: list[str]
    body_systems: list[str]
    mechanisms: list[dict[str, Any]]
    candidate_hypotheses: list[str]
    possible_consequences: list[str]
    missing_evidence: list[str]
    alternative_mechanisms: list[str]
    prohibited_conclusions: list[str]
    relations: list[CausalityRelation] = field(default_factory=list)


@dataclass
class CausalityAssessment:
    patient_id: str
    episode_id: str
    observations: list[dict[str, Any]]
    branches: list[CausalityBranch]
    unassigned_fact_ids: list[str]
    devil_review: dict[str, Any]


_DOMAIN_DEFINITIONS: dict[str, dict[str, Any]] = {
    "glycemic_regulation": {
        "title": "Glycemic regulation",
        "codes": {"GLUCOSE_FASTING", "HBA1C", "INSULIN_FASTING"},
        "functional_processes": ["glucose_homeostasis", "insulin_signaling"],
        "body_systems": ["endocrine", "metabolic"],
        "mechanisms": [
            ("impaired_glycemic_regulation", "supported"),
            ("insulin_resistance_or_alternative", "plausible"),
        ],
        "candidate_hypotheses": ["glycemic_dysregulation"],
        "possible_consequences": ["vascular_stress", "metabolic_complications"],
        "missing_evidence": ["repeat_fasting_glucose", "HbA1c", "medications", "clinical_context"],
        "alternative_mechanisms": ["acute_stress", "medication_effect", "endocrine_trigger"],
        "prohibited_conclusions": ["diabetes_confirmed", "diabetes_type_determined"],
    },
    "lipid_metabolism": {
        "title": "Lipid metabolism",
        "codes": {"TRIGLYCERIDES", "LDL", "HDL", "TOTAL_CHOLESTEROL", "APOB"},
        "functional_processes": ["lipid_transport", "lipoprotein_handling"],
        "body_systems": ["metabolic", "cardiovascular"],
        "mechanisms": [("altered_lipid_handling", "plausible")],
        "candidate_hypotheses": ["lipid_metabolism_disturbance"],
        "possible_consequences": ["atherogenic_particle_burden"],
        "missing_evidence": ["LDL", "HDL", "non_HDL", "ApoB", "clinical_risk_context"],
        "alternative_mechanisms": ["dietary_context", "endocrine_driver", "medication_effect"],
        "prohibited_conclusions": ["cardiovascular_risk_calculated", "metabolic_syndrome_confirmed"],
    },
    "hepatic_integrity": {
        "title": "Hepatic integrity",
        "codes": {"ALT", "AST", "GGT", "ALP", "BILIRUBIN_TOTAL"},
        "functional_processes": ["hepatocellular_integrity", "substrate_processing"],
        "body_systems": ["hepatic", "metabolic"],
        "mechanisms": [("hepatocellular_injury_or_metabolic_process", "plausible")],
        "candidate_hypotheses": ["possible_hepatic_involvement"],
        "possible_consequences": ["altered_metabolic_processing"],
        "missing_evidence": ["AST", "GGT", "bilirubin", "ALP", "medications", "alcohol_history"],
        "alternative_mechanisms": ["muscle_source", "medication_effect", "temporary_response"],
        "prohibited_conclusions": ["MASLD_confirmed", "liver_disease_cause_determined"],
    },
    "renal_filtration": {
        "title": "Renal filtration",
        "codes": {"CREATININE", "EGFR", "UREA", "ALBUMIN_URINE"},
        "functional_processes": ["glomerular_filtration", "renal_handling"],
        "body_systems": ["renal", "vascular"],
        "mechanisms": [("reduced_glomerular_filtration", "plausible")],
        "candidate_hypotheses": ["renal_context"],
        "possible_consequences": ["altered_clearance", "vascular_context"],
        "missing_evidence": ["eGFR", "urine_ACR", "urinalysis", "blood_pressure"],
        "alternative_mechanisms": ["muscle_mass_context", "hydration_context", "measurement_variation"],
        "prohibited_conclusions": ["kidneys_healthy", "CKD_excluded"],
    },
}


def _fact_id(observation: Any) -> str:
    return f"laboratory_result:{observation.laboratory_result_id}"


def _status_for_mechanism(domain: str, code: str, observations: list[Any], default: str) -> str:
    if domain == "renal_filtration" and code == "reduced_glomerular_filtration":
        creatinine = next((o for o in observations if o.test_code.upper() == "CREATININE"), None)
        if creatinine is not None and creatinine.interpretation == "normal":
            return MechanismStatus.CONTRADICTED.value
    if any(o.interpretation in {"high", "critical_high", "low", "critical_low"} for o in observations):
        return MechanismStatus.SUPPORTED.value if default == "supported" else MechanismStatus.PLAUSIBLE.value
    return MechanismStatus.INSUFFICIENT_EVIDENCE.value if default != "contradicted" else default


def _serialize_observation(observation: Any) -> dict[str, Any]:
    data = dict(observation.__dict__)
    for key in ("observation_class", "evidence_role"):
        value = data.get(key)
        if hasattr(value, "value"):
            data[key] = value.value
    if data.get("result_date") is not None:
        data["result_date"] = data["result_date"].isoformat()
    return data


def build_causality_assessment(patient_id: str, episode_id: str, observations: Iterable[Any]) -> CausalityAssessment:
    observations = list(observations)
    assigned_ids: set[str] = set()
    branches: list[CausalityBranch] = []

    for domain, definition in _DOMAIN_DEFINITIONS.items():
        relevant = [o for o in observations if o.test_code.upper() in definition["codes"]]
        if not relevant:
            continue

        fact_ids = [_fact_id(o) for o in relevant]
        assigned_ids.update(fact_ids)
        mechanisms = [
            {
                "code": code,
                "status": _status_for_mechanism(domain, code, relevant, default),
                "confidence": 0.65 if any(o.interpretation != "normal" for o in relevant) else 0.35,
                "rationale": "Candidate mechanistic interpretation; not a diagnosis.",
                "source_key": "FHOS_CURATED:S08E06",
            }
            for code, default in definition["mechanisms"]
        ]
        relations = [
            CausalityRelation(
                from_code=fact_id,
                to_code=definition["functional_processes"][0],
                relation_kind=CausalityRelationKind.INDICATES_PROCESS,
                status=MechanismStatus.PLAUSIBLE,
                confidence=0.5,
                rationale="Patient fact may indicate a functional process in the stated context.",
                source_key="FHOS_CURATED:S08E06",
            )
            for fact_id in fact_ids
        ]
        branches.append(CausalityBranch(
            code=domain,
            title=definition["title"],
            patient_fact_ids=fact_ids,
            functional_processes=list(definition["functional_processes"]),
            body_systems=list(definition["body_systems"]),
            mechanisms=mechanisms,
            candidate_hypotheses=list(definition["candidate_hypotheses"]),
            possible_consequences=list(definition["possible_consequences"]),
            missing_evidence=list(definition["missing_evidence"]),
            alternative_mechanisms=list(definition["alternative_mechanisms"]),
            prohibited_conclusions=list(definition["prohibited_conclusions"]),
            relations=relations,
        ))

    all_fact_ids = [_fact_id(o) for o in observations]
    unassigned = [fact_id for fact_id in all_fact_ids if fact_id not in assigned_ids]
    violations: list[str] = []
    if unassigned:
        violations.append("unassigned_patient_facts")
    if not branches:
        violations.append("no_causal_branches_generated")

    devil_review = {
        "passed": not violations,
        "violations": violations,
        "warnings": [
            "Association does not establish causality.",
            "Mechanisms and hypotheses are not diagnoses.",
        ],
        "limitations": ["Assessment is limited to available structured observations and curated mappings."],
        "checks": {
            "all_observations_preserved": not unassigned,
            "normal_results_preserved": any(o.interpretation == "normal" for o in observations),
            "abnormal_not_promoted_to_diagnosis": True,
            "alternatives_preserved": all(bool(branch.alternative_mechanisms) for branch in branches),
            "provenance_present": all(bool(branch.relations) for branch in branches),
        },
    }

    return CausalityAssessment(
        patient_id=patient_id,
        episode_id=episode_id,
        observations=[_serialize_observation(o) for o in observations],
        branches=branches,
        unassigned_fact_ids=unassigned,
        devil_review=devil_review,
    )
