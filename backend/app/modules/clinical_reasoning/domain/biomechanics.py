from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable

from .causality import ContextConstraint, ProvenanceReference
from .hypothesis_expansion import (
    BranchRelationship,
    BranchRelationshipType,
    BranchStatus,
    HypothesisBranch,
)


class BiomechanicalFactKind(str, Enum):
    SYMPTOM = "symptom"
    FUNCTIONAL_LIMITATION = "functional_limitation"
    LOAD_EXPOSURE = "load_exposure"
    MOVEMENT_PATTERN = "movement_pattern"
    PHYSICAL_FINDING = "physical_finding"
    TRAUMA_HISTORY = "trauma_history"
    PROCEDURE_HISTORY = "procedure_history"
    IMAGING_FINDING = "imaging_finding"
    RED_FLAG = "red_flag"
    CONTEXT = "context"


@dataclass(frozen=True)
class BiomechanicalFact:
    id: str
    kind: BiomechanicalFactKind
    code: str
    value: str | float | bool
    laterality: str | None = None
    body_region: str | None = None
    provenance: list[ProvenanceReference] = field(default_factory=list)
    context_constraints: list[ContextConstraint] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.id.strip() or not self.code.strip():
            raise ValueError("biomechanical fact requires id and code")
        if not self.provenance:
            raise ValueError("biomechanical fact requires provenance")


@dataclass(frozen=True)
class BiomechanicalBranchTemplate:
    code: str
    title: str
    causal_domain: str
    branch_type: str
    trigger_codes: frozenset[str]
    contradicting_codes: frozenset[str] = frozenset()
    missing_evidence_codes: tuple[str, ...] = ()
    safety_critical: bool = False


@dataclass
class BiomechanicsExpansionResult:
    case_id: str
    branches: list[HypothesisBranch]
    relationships: list[BranchRelationship]
    unassigned_fact_ids: list[str]
    red_flag_branch_ids: list[str]
    missing_evidence_ids: list[str]
    limitations: list[str]
    prohibited_conclusions: list[str]


DEFAULT_HIP_COMPLEX_TEMPLATES: tuple[BiomechanicalBranchTemplate, ...] = (
    BiomechanicalBranchTemplate(
        "local_joint", "Local hip joint mechanism", "local_joint", "primary_mechanistic",
        frozenset({"groin_pain", "limited_internal_rotation", "pain_with_weight_bearing", "hip_joint_imaging_change"}),
        missing_evidence_codes=("hip_range_of_motion", "joint_specific_exam", "hip_imaging_context"),
    ),
    BiomechanicalBranchTemplate(
        "muscle_tendon", "Muscle-tendon mechanism", "muscle_tendon", "alternative_mechanistic",
        frozenset({"lateral_hip_pain", "pain_with_resisted_abduction", "tendon_load_pain", "focal_tenderness"}),
        missing_evidence_codes=("resisted_strength_testing", "tendon_palpation", "load_response"),
    ),
    BiomechanicalBranchTemplate(
        "lumbar_radicular", "Lumbar-radicular mechanism", "lumbar_radicular", "alternative_mechanistic",
        frozenset({"radiating_leg_pain", "neurological_deficit", "positive_neural_tension", "back_pain"}),
        missing_evidence_codes=("neurological_exam", "neural_tension_testing", "lumbar_context"),
        safety_critical=True,
    ),
    BiomechanicalBranchTemplate(
        "biomechanical_load", "Biomechanical load and movement-pattern mechanism", "biomechanical_load", "contributing",
        frozenset({"occupational_load", "repetitive_load", "gait_asymmetry", "movement_pattern_change", "training_load_spike"}),
        missing_evidence_codes=("load_history", "gait_assessment", "movement_observation"),
    ),
    BiomechanicalBranchTemplate(
        "degenerative", "Degenerative structural mechanism", "degenerative", "alternative_mechanistic",
        frozenset({"progressive_stiffness", "age_related_change", "degenerative_imaging", "activity_related_pain"}),
        missing_evidence_codes=("symptom_imaging_correlation", "functional_progression", "prior_imaging_comparison"),
    ),
    BiomechanicalBranchTemplate(
        "inflammatory", "Inflammatory mechanism", "inflammatory", "safety_alternative",
        frozenset({"morning_stiffness", "night_pain", "systemic_inflammatory_features", "multiple_joint_involvement"}),
        missing_evidence_codes=("inflammatory_history", "systemic_review", "targeted_laboratory_context"),
        safety_critical=True,
    ),
    BiomechanicalBranchTemplate(
        "vascular", "Vascular mechanism", "vascular", "safety_alternative",
        frozenset({"limb_swelling", "color_change", "temperature_change", "exertional_cramping", "vascular_risk_context"}),
        missing_evidence_codes=("vascular_exam", "pulse_assessment", "urgent_vascular_context"),
        safety_critical=True,
    ),
    BiomechanicalBranchTemplate(
        "traumatic", "Traumatic mechanism", "traumatic", "alternative_mechanistic",
        frozenset({"recent_fall", "direct_impact", "sudden_load_injury", "inability_to_weight_bear"}),
        missing_evidence_codes=("trauma_timeline", "fracture_screen", "post_trauma_imaging_context"),
        safety_critical=True,
    ),
    BiomechanicalBranchTemplate(
        "referred_pain", "Referred pain mechanism", "referred_pain", "alternative_mechanistic",
        frozenset({"pain_not_reproduced_at_hip", "abdominal_pelvic_symptom", "lumbar_referred_pattern", "visceral_context"}),
        missing_evidence_codes=("source_region_exam", "abdominal_pelvic_review", "referred_pattern_testing"),
    ),
    BiomechanicalBranchTemplate(
        "iatrogenic_or_postoperative", "Iatrogenic or postoperative mechanism", "iatrogenic_or_postoperative", "contextual",
        frozenset({"recent_procedure", "implant_present", "postoperative_onset", "medication_related_weakness"}),
        missing_evidence_codes=("procedure_timeline", "implant_context", "postoperative_complication_screen"),
        safety_critical=True,
    ),
)


class HipComplexExpansionEngine:
    """First non-laboratory vertical slice for hip/lumbar-pelvic-hip complaints.

    The engine expands facts into independent mechanistic branches. It does not
    diagnose, select treatment, or treat imaging findings as symptom causation.
    """

    def expand(
        self,
        case_id: str,
        facts: Iterable[BiomechanicalFact],
        templates: Iterable[BiomechanicalBranchTemplate] = DEFAULT_HIP_COMPLEX_TEMPLATES,
    ) -> BiomechanicsExpansionResult:
        fact_list = list(facts)
        template_list = list(templates)
        fact_by_code: dict[str, list[BiomechanicalFact]] = {}
        for fact in fact_list:
            fact_by_code.setdefault(fact.code, []).append(fact)

        branches: list[HypothesisBranch] = []
        assigned_fact_ids: set[str] = set()
        all_missing: set[str] = set()

        for template in template_list:
            supporting = [
                fact for code in template.trigger_codes for fact in fact_by_code.get(code, [])
            ]
            contradicting = [
                fact for code in template.contradicting_codes for fact in fact_by_code.get(code, [])
            ]
            if not supporting and not template.safety_critical:
                continue
            if not supporting and template.safety_critical:
                red_flags = [f for f in fact_list if f.kind == BiomechanicalFactKind.RED_FLAG]
                if not red_flags:
                    continue
                supporting = red_flags

            assigned_fact_ids.update(f.id for f in supporting + contradicting)
            missing = [f"{case_id}:missing:{template.code}:{code}" for code in template.missing_evidence_codes]
            all_missing.update(missing)
            provenance = self._merge_provenance(supporting + contradicting)
            constraints = [c for fact in supporting + contradicting for c in fact.context_constraints]
            confidence = min(0.85, 0.35 + 0.1 * len({f.code for f in supporting}))
            status = BranchStatus.UNSAFE_TO_CLOSE if template.safety_critical else BranchStatus.ACTIVE
            branches.append(HypothesisBranch(
                id=f"{case_id}:biomechanics:{template.code}",
                case_id=case_id,
                title=template.title,
                description="Candidate biomechanics/MSK mechanism; not a diagnosis.",
                root_trigger_ids=[f.id for f in supporting],
                causal_domain=template.causal_domain,
                branch_type=template.branch_type,
                node_ids=[f.id for f in supporting] + [f"mechanism:{template.code}"] + missing,
                edge_ids=[f"{case_id}:edge:{template.code}:{i}" for i in range(max(1, len(supporting)))],
                supporting_fact_ids=[f.id for f in supporting],
                contradicting_fact_ids=[f.id for f in contradicting],
                missing_evidence_ids=missing,
                evidence_strength="plausible" if supporting else "speculative",
                confidence=confidence,
                status=status,
                provenance=provenance,
                context_constraints=constraints,
                safety_critical=template.safety_critical,
            ))

        relationships = self._relationships(branches)
        red_flag_branch_ids = sorted(b.id for b in branches if b.safety_critical)
        unassigned = sorted(f.id for f in fact_list if f.id not in assigned_fact_ids)
        return BiomechanicsExpansionResult(
            case_id=case_id,
            branches=branches,
            relationships=relationships,
            unassigned_fact_ids=unassigned,
            red_flag_branch_ids=red_flag_branch_ids,
            missing_evidence_ids=sorted(all_missing),
            limitations=[
                "Symptom location alone does not establish anatomical source.",
                "Imaging change may be incidental and requires symptom-context correlation.",
                "Biomechanical association does not establish causality.",
                "Safety-critical alternatives remain visible until adequately assessed.",
            ],
            prohibited_conclusions=[
                "diagnosis_confirmed",
                "imaging_explains_symptoms_automatically",
                "single_mechanical_cause_confirmed",
                "pain_severity_equals_tissue_damage",
                "normal_imaging_excludes_functional_mechanism",
            ],
        )

    @staticmethod
    def _merge_provenance(facts: list[BiomechanicalFact]) -> list[ProvenanceReference]:
        merged: dict[tuple[str, str, str | None], ProvenanceReference] = {}
        for fact in facts:
            for ref in fact.provenance:
                merged[(ref.source_id, ref.source_version, ref.locator)] = ref
        if not merged:
            raise ValueError("generated branch requires provenance")
        return list(merged.values())

    @staticmethod
    def _relationships(branches: list[HypothesisBranch]) -> list[BranchRelationship]:
        relations: list[BranchRelationship] = []
        for index, left in enumerate(branches):
            for right in branches[index + 1:]:
                provenance = list({
                    (ref.source_id, ref.source_version, ref.locator): ref
                    for ref in left.provenance + right.provenance
                }.values())
                relation_type = (
                    BranchRelationshipType.REQUIRES_EXCLUSION_OF
                    if left.safety_critical or right.safety_critical
                    else BranchRelationshipType.MAY_COEXIST_WITH
                )
                relations.append(BranchRelationship(
                    id=f"{left.id}->{right.id}",
                    source_branch_id=left.id,
                    target_branch_id=right.id,
                    relationship_type=relation_type,
                    explanation="Hip-region mechanisms may coexist or compete and require separate verification.",
                    evidence_strength="plausible",
                    confidence=0.5,
                    provenance=provenance,
                ))
        return relations
