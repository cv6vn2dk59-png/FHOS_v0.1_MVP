from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable

from .causality import ContextConstraint, ProvenanceReference
from .hypothesis_expansion import HypothesisBranch


class ExaminationFindingKind(str, Enum):
    ACTIVE_RANGE_OF_MOTION = "active_range_of_motion"
    PASSIVE_RANGE_OF_MOTION = "passive_range_of_motion"
    RESISTED_TEST = "resisted_test"
    PROVOCATION_TEST = "provocation_test"
    PALPATION = "palpation"
    GAIT = "gait"
    NEUROLOGICAL = "neurological"
    VASCULAR = "vascular"
    FUNCTIONAL_TASK = "functional_task"
    OBSERVATION = "observation"


class FindingResult(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    EQUIVOCAL = "equivocal"
    NOT_PERFORMED = "not_performed"
    UNKNOWN = "unknown"


class BranchExaminationEffectType(str, Enum):
    SUPPORTS = "supports"
    WEAKENS = "weakens"
    CONTRADICTS = "contradicts"
    NON_DISCRIMINATING = "non_discriminating"
    CHANGES_URGENCY = "changes_urgency"


@dataclass(frozen=True)
class ExaminationFinding:
    id: str
    kind: ExaminationFindingKind
    code: str
    result: FindingResult
    value: Any = None
    body_region: str | None = None
    laterality: str | None = None
    provenance: list[ProvenanceReference] = field(default_factory=list)
    context_constraints: list[ContextConstraint] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.id.strip() or not self.code.strip():
            raise ValueError("examination finding requires id and code")
        if not self.provenance:
            raise ValueError("examination finding requires provenance")


@dataclass(frozen=True)
class ExaminationRule:
    code: str
    positive_supports: frozenset[str] = frozenset()
    positive_weakens: frozenset[str] = frozenset()
    negative_weakens: frozenset[str] = frozenset()
    non_discriminating_for: frozenset[str] = frozenset()
    urgency_domains: frozenset[str] = frozenset()
    rationale: str = ""


@dataclass(frozen=True)
class BranchExaminationEffect:
    branch_id: str
    finding_id: str
    effect_type: BranchExaminationEffectType
    strength: str
    rationale: str
    provenance: list[ProvenanceReference]
    context_constraints: list[ContextConstraint] = field(default_factory=list)


@dataclass(frozen=True)
class MissingExaminationEvidence:
    id: str
    branch_id: str
    required_code: str
    rationale: str
    provenance: list[ProvenanceReference]


@dataclass
class BranchExaminationAssessment:
    branch_id: str
    supporting_finding_ids: list[str]
    weakening_finding_ids: list[str]
    contradicting_finding_ids: list[str]
    non_discriminating_finding_ids: list[str]
    urgency_finding_ids: list[str]
    missing_evidence_ids: list[str]


@dataclass
class BiomechanicalExaminationResult:
    case_id: str
    effects: list[BranchExaminationEffect]
    branch_assessments: list[BranchExaminationAssessment]
    missing_evidence: list[MissingExaminationEvidence]
    safety_escalation_branch_ids: list[str]
    unassigned_finding_ids: list[str]
    limitations: list[str]
    prohibited_conclusions: list[str]


DEFAULT_EXAMINATION_RULES: tuple[ExaminationRule, ...] = (
    ExaminationRule(
        "limited_internal_rotation",
        positive_supports=frozenset({"local_joint", "degenerative"}),
        negative_weakens=frozenset({"local_joint", "degenerative"}),
        rationale="Restricted hip internal rotation may support a joint/structural branch but is not a diagnosis.",
    ),
    ExaminationRule(
        "pain_with_passive_hip_motion",
        positive_supports=frozenset({"local_joint", "inflammatory"}),
        negative_weakens=frozenset({"local_joint"}),
        rationale="Pain with passive motion may support an intra-articular or inflammatory mechanism.",
    ),
    ExaminationRule(
        "pain_with_resisted_abduction",
        positive_supports=frozenset({"muscle_tendon"}),
        negative_weakens=frozenset({"muscle_tendon"}),
        rationale="Pain with resisted abduction may support a muscle-tendon load response.",
    ),
    ExaminationRule(
        "focal_tenderness",
        positive_supports=frozenset({"muscle_tendon"}),
        non_discriminating_for=frozenset({"local_joint", "degenerative"}),
        rationale="Focal tenderness may support local tissue sensitivity but does not confirm the pain generator.",
    ),
    ExaminationRule(
        "positive_neural_tension",
        positive_supports=frozenset({"lumbar_radicular"}),
        negative_weakens=frozenset({"lumbar_radicular"}),
        rationale="Neural tension reproduction may support a neural mechanism but is not diagnostic alone.",
    ),
    ExaminationRule(
        "neurological_deficit",
        positive_supports=frozenset({"lumbar_radicular"}),
        urgency_domains=frozenset({"lumbar_radicular"}),
        rationale="Objective neurological deficit changes urgency and requires separate clinical assessment.",
    ),
    ExaminationRule(
        "gait_asymmetry",
        positive_supports=frozenset({"biomechanical_load"}),
        non_discriminating_for=frozenset({"local_joint", "muscle_tendon", "degenerative"}),
        rationale="Gait asymmetry supports a movement/load context but does not identify a single tissue source.",
    ),
    ExaminationRule(
        "pain_not_reproduced_at_hip",
        positive_supports=frozenset({"referred_pain"}),
        positive_weakens=frozenset({"local_joint"}),
        rationale="Failure to reproduce symptoms locally may weaken a local-joint branch and support source-region review.",
    ),
    ExaminationRule(
        "absent_or_reduced_pulse",
        positive_supports=frozenset({"vascular"}),
        urgency_domains=frozenset({"vascular"}),
        rationale="Abnormal distal pulse findings change urgency for a vascular branch.",
    ),
    ExaminationRule(
        "unilateral_limb_swelling",
        positive_supports=frozenset({"vascular"}),
        urgency_domains=frozenset({"vascular", "iatrogenic_or_postoperative"}),
        rationale="Unilateral swelling may require urgent vascular or postoperative assessment.",
    ),
    ExaminationRule(
        "inability_to_weight_bear",
        positive_supports=frozenset({"traumatic"}),
        urgency_domains=frozenset({"traumatic"}),
        rationale="Inability to bear weight after a relevant event changes urgency for traumatic mechanisms.",
    ),
    ExaminationRule(
        "postoperative_wound_change",
        positive_supports=frozenset({"iatrogenic_or_postoperative"}),
        urgency_domains=frozenset({"iatrogenic_or_postoperative"}),
        rationale="Postoperative wound change requires dedicated complication assessment.",
    ),
)


REQUIRED_EXAMINATION_BY_DOMAIN: dict[str, tuple[str, ...]] = {
    "local_joint": ("hip_active_rom", "hip_passive_rom", "joint_specific_provocation"),
    "muscle_tendon": ("resisted_strength_testing", "tendon_palpation", "load_response"),
    "lumbar_radicular": ("neurological_exam", "neural_tension_testing", "lumbar_movement_exam"),
    "biomechanical_load": ("gait_assessment", "functional_task_observation", "load_response"),
    "degenerative": ("active_passive_rom_comparison", "functional_progression"),
    "inflammatory": ("inflammatory_pattern_exam", "systemic_review"),
    "vascular": ("pulse_assessment", "vascular_observation"),
    "traumatic": ("weight_bearing_assessment", "fracture_screen"),
    "referred_pain": ("source_region_exam", "referred_pattern_testing"),
    "iatrogenic_or_postoperative": ("postoperative_exam", "implant_or_wound_context"),
}


class BiomechanicalExaminationEngine:
    """Maps examination findings to branch-level evidence effects.

    A finding changes support, contradiction or urgency; it never confirms a
    diagnosis or a tissue source by itself. Missing examination data remains
    explicit and is never converted into a negative result.
    """

    def evaluate(
        self,
        case_id: str,
        branches: Iterable[HypothesisBranch],
        findings: Iterable[ExaminationFinding],
        rules: Iterable[ExaminationRule] = DEFAULT_EXAMINATION_RULES,
    ) -> BiomechanicalExaminationResult:
        branch_list = list(branches)
        finding_list = list(findings)
        rule_by_code = {rule.code: rule for rule in rules}
        branch_by_domain = {branch.causal_domain: branch for branch in branch_list}
        effects: list[BranchExaminationEffect] = []
        assigned_finding_ids: set[str] = set()
        safety_branch_ids: set[str] = set()

        for finding in finding_list:
            rule = rule_by_code.get(finding.code)
            if rule is None or finding.result in {FindingResult.NOT_PERFORMED, FindingResult.UNKNOWN}:
                continue

            domains_and_effects: list[tuple[frozenset[str], BranchExaminationEffectType, str]] = []
            if finding.result == FindingResult.POSITIVE:
                domains_and_effects.extend([
                    (rule.positive_supports, BranchExaminationEffectType.SUPPORTS, "moderate"),
                    (rule.positive_weakens, BranchExaminationEffectType.WEAKENS, "moderate"),
                    (rule.non_discriminating_for, BranchExaminationEffectType.NON_DISCRIMINATING, "contextual"),
                    (rule.urgency_domains, BranchExaminationEffectType.CHANGES_URGENCY, "high"),
                ])
            elif finding.result == FindingResult.NEGATIVE:
                domains_and_effects.append(
                    (rule.negative_weakens, BranchExaminationEffectType.WEAKENS, "weak")
                )
            else:
                domains_and_effects.append(
                    (frozenset(branch_by_domain), BranchExaminationEffectType.NON_DISCRIMINATING, "weak")
                )

            for domains, effect_type, strength in domains_and_effects:
                for domain in domains:
                    branch = branch_by_domain.get(domain)
                    if branch is None:
                        continue
                    assigned_finding_ids.add(finding.id)
                    if effect_type == BranchExaminationEffectType.CHANGES_URGENCY:
                        safety_branch_ids.add(branch.id)
                    effects.append(BranchExaminationEffect(
                        branch_id=branch.id,
                        finding_id=finding.id,
                        effect_type=effect_type,
                        strength=strength,
                        rationale=rule.rationale,
                        provenance=finding.provenance,
                        context_constraints=finding.context_constraints,
                    ))

        missing_evidence: list[MissingExaminationEvidence] = []
        observed_codes = {
            finding.code for finding in finding_list
            if finding.result not in {FindingResult.NOT_PERFORMED, FindingResult.UNKNOWN}
        }
        provenance = self._aggregate_provenance(branch_list, finding_list)
        for branch in branch_list:
            for required_code in REQUIRED_EXAMINATION_BY_DOMAIN.get(branch.causal_domain, ()):
                if required_code in observed_codes:
                    continue
                missing_evidence.append(MissingExaminationEvidence(
                    id=f"{case_id}:missing-exam:{branch.causal_domain}:{required_code}",
                    branch_id=branch.id,
                    required_code=required_code,
                    rationale="Examination item was not supplied; absence of data is not a negative finding.",
                    provenance=provenance,
                ))

        assessments = [self._assessment(branch, effects, missing_evidence) for branch in branch_list]
        return BiomechanicalExaminationResult(
            case_id=case_id,
            effects=effects,
            branch_assessments=assessments,
            missing_evidence=missing_evidence,
            safety_escalation_branch_ids=sorted(safety_branch_ids),
            unassigned_finding_ids=sorted(f.id for f in finding_list if f.id not in assigned_finding_ids),
            limitations=[
                "Provocation findings depend on technique, context, and symptom interpretation.",
                "Pain reproduction does not confirm a unique tissue source.",
                "A negative examination finding may weaken but does not automatically exclude a branch.",
                "Range-of-motion restriction is a finding, not a causal explanation by itself.",
            ],
            prohibited_conclusions=[
                "provocation_test_confirms_diagnosis",
                "pain_reproduction_confirms_tissue_source",
                "negative_test_absolutely_excludes_branch",
                "range_of_motion_restriction_is_cause",
                "single_examination_finding_selects_treatment",
            ],
        )

    @staticmethod
    def _aggregate_provenance(
        branches: list[HypothesisBranch], findings: list[ExaminationFinding]
    ) -> list[ProvenanceReference]:
        values: dict[tuple[str, str, str | None], ProvenanceReference] = {}
        for branch in branches:
            for item in branch.provenance:
                values[(item.source_id, item.source_version, item.locator)] = item
        for finding in findings:
            for item in finding.provenance:
                values[(item.source_id, item.source_version, item.locator)] = item
        if not values:
            raise ValueError("examination assessment requires provenance")
        return list(values.values())

    @staticmethod
    def _assessment(
        branch: HypothesisBranch,
        effects: list[BranchExaminationEffect],
        missing: list[MissingExaminationEvidence],
    ) -> BranchExaminationAssessment:
        relevant = [effect for effect in effects if effect.branch_id == branch.id]
        return BranchExaminationAssessment(
            branch_id=branch.id,
            supporting_finding_ids=sorted({e.finding_id for e in relevant if e.effect_type == BranchExaminationEffectType.SUPPORTS}),
            weakening_finding_ids=sorted({e.finding_id for e in relevant if e.effect_type == BranchExaminationEffectType.WEAKENS}),
            contradicting_finding_ids=sorted({e.finding_id for e in relevant if e.effect_type == BranchExaminationEffectType.CONTRADICTS}),
            non_discriminating_finding_ids=sorted({e.finding_id for e in relevant if e.effect_type == BranchExaminationEffectType.NON_DISCRIMINATING}),
            urgency_finding_ids=sorted({e.finding_id for e in relevant if e.effect_type == BranchExaminationEffectType.CHANGES_URGENCY}),
            missing_evidence_ids=sorted(item.id for item in missing if item.branch_id == branch.id),
        )
