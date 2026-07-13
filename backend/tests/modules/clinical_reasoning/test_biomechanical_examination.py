from app.modules.clinical_reasoning.domain.biomechanical_examination import (
    BiomechanicalExaminationEngine,
    BranchExaminationEffectType,
    ExaminationFinding,
    ExaminationFindingKind,
    FindingResult,
)
from app.modules.clinical_reasoning.domain.causality import ProvenanceReference
from app.modules.clinical_reasoning.domain.hypothesis_expansion import BranchStatus, HypothesisBranch

PROV = [ProvenanceReference("clinician_exam", "S08E13", "TEST-EXAM")]


def branch(domain: str, safety: bool = False) -> HypothesisBranch:
    return HypothesisBranch(
        id=f"b:{domain}", case_id="CASE-1", title=domain, description="candidate; not diagnosis",
        root_trigger_ids=["fact"], causal_domain=domain, branch_type="alternative_mechanistic",
        node_ids=["fact", f"mechanism:{domain}"], edge_ids=[f"edge:{domain}"],
        evidence_strength="plausible", confidence=0.5,
        status=BranchStatus.UNSAFE_TO_CLOSE if safety else BranchStatus.ACTIVE,
        provenance=PROV, safety_critical=safety,
    )


def finding(code: str, result: FindingResult = FindingResult.POSITIVE, id_: str = "f1") -> ExaminationFinding:
    return ExaminationFinding(id_, ExaminationFindingKind.PROVOCATION_TEST, code, result, provenance=PROV)


def test_positive_provocation_supports_branch_without_diagnosis():
    result = BiomechanicalExaminationEngine().evaluate("CASE-1", [branch("muscle_tendon")], [finding("pain_with_resisted_abduction")])
    assert any(e.effect_type == BranchExaminationEffectType.SUPPORTS for e in result.effects)
    assert "provocation_test_confirms_diagnosis" in result.prohibited_conclusions


def test_negative_test_weakens_but_does_not_exclude_branch():
    result = BiomechanicalExaminationEngine().evaluate("CASE-1", [branch("lumbar_radicular", True)], [finding("positive_neural_tension", FindingResult.NEGATIVE)])
    assessment = result.branch_assessments[0]
    assert assessment.weakening_finding_ids == ["f1"]
    assert assessment.contradicting_finding_ids == []
    assert "negative_test_absolutely_excludes_branch" in result.prohibited_conclusions


def test_rom_restriction_supports_multiple_branches_not_single_cause():
    result = BiomechanicalExaminationEngine().evaluate("CASE-1", [branch("local_joint"), branch("degenerative")], [finding("limited_internal_rotation")])
    assert {e.branch_id for e in result.effects if e.effect_type == BranchExaminationEffectType.SUPPORTS} == {"b:local_joint", "b:degenerative"}
    assert "range_of_motion_restriction_is_cause" in result.prohibited_conclusions


def test_gait_asymmetry_is_supporting_and_non_discriminating():
    result = BiomechanicalExaminationEngine().evaluate("CASE-1", [branch("biomechanical_load"), branch("local_joint")], [finding("gait_asymmetry")])
    types = {(e.branch_id, e.effect_type) for e in result.effects}
    assert ("b:biomechanical_load", BranchExaminationEffectType.SUPPORTS) in types
    assert ("b:local_joint", BranchExaminationEffectType.NON_DISCRIMINATING) in types


def test_neurological_deficit_escalates_safety_branch():
    result = BiomechanicalExaminationEngine().evaluate("CASE-1", [branch("lumbar_radicular", True)], [finding("neurological_deficit")])
    assert result.safety_escalation_branch_ids == ["b:lumbar_radicular"]
    assert result.branch_assessments[0].urgency_finding_ids == ["f1"]


def test_vascular_finding_changes_urgency():
    result = BiomechanicalExaminationEngine().evaluate("CASE-1", [branch("vascular", True)], [finding("absent_or_reduced_pulse")])
    assert result.safety_escalation_branch_ids == ["b:vascular"]


def test_trauma_weight_bearing_finding_changes_urgency():
    result = BiomechanicalExaminationEngine().evaluate("CASE-1", [branch("traumatic", True)], [finding("inability_to_weight_bear")])
    assert result.safety_escalation_branch_ids == ["b:traumatic"]


def test_missing_exam_data_is_not_negative_result():
    result = BiomechanicalExaminationEngine().evaluate("CASE-1", [branch("local_joint")], [])
    assert result.effects == []
    assert len(result.missing_evidence) == 3
    assert result.branch_assessments[0].weakening_finding_ids == []


def test_not_performed_finding_remains_unassigned_and_missing():
    result = BiomechanicalExaminationEngine().evaluate("CASE-1", [branch("vascular", True)], [finding("absent_or_reduced_pulse", FindingResult.NOT_PERFORMED)])
    assert result.unassigned_finding_ids == ["f1"]
    assert result.safety_escalation_branch_ids == []
    assert result.missing_evidence


def test_pain_not_reproduced_supports_referred_and_weakens_local():
    result = BiomechanicalExaminationEngine().evaluate("CASE-1", [branch("referred_pain"), branch("local_joint")], [finding("pain_not_reproduced_at_hip")])
    types = {(e.branch_id, e.effect_type) for e in result.effects}
    assert ("b:referred_pain", BranchExaminationEffectType.SUPPORTS) in types
    assert ("b:local_joint", BranchExaminationEffectType.WEAKENS) in types


def test_unknown_finding_is_preserved_as_unassigned():
    result = BiomechanicalExaminationEngine().evaluate("CASE-1", [branch("local_joint")], [finding("unknown_test")])
    assert result.unassigned_finding_ids == ["f1"]


def test_examination_finding_requires_provenance():
    try:
        ExaminationFinding("f", ExaminationFindingKind.OBSERVATION, "code", FindingResult.POSITIVE)
    except ValueError as exc:
        assert "provenance" in str(exc)
    else:
        raise AssertionError("expected provenance validation")
