from app.modules.clinical_reasoning.domain.biomechanics import (
    BiomechanicalFact,
    BiomechanicalFactKind,
    HipComplexExpansionEngine,
)
from app.modules.clinical_reasoning.domain.causality import ProvenanceReference
from app.modules.clinical_reasoning.domain.hypothesis_expansion import BranchStatus


PROV = [ProvenanceReference("patient_report", "S08E12", "TEST-HIP-001")]


def fact(id_, kind, code, value=True):
    return BiomechanicalFact(id_, kind, code, value, body_region="hip", provenance=PROV)


def test_hip_pain_expands_multiple_independent_branches():
    result = HipComplexExpansionEngine().expand("HIP-001", [
        fact("f1", BiomechanicalFactKind.SYMPTOM, "groin_pain"),
        fact("f2", BiomechanicalFactKind.PHYSICAL_FINDING, "limited_internal_rotation"),
        fact("f3", BiomechanicalFactKind.LOAD_EXPOSURE, "occupational_load"),
        fact("f4", BiomechanicalFactKind.SYMPTOM, "back_pain"),
    ])
    domains = {branch.causal_domain for branch in result.branches}
    assert {"local_joint", "biomechanical_load", "lumbar_radicular"}.issubset(domains)


def test_imaging_change_is_not_a_diagnosis():
    result = HipComplexExpansionEngine().expand("HIP-002", [
        fact("f1", BiomechanicalFactKind.IMAGING_FINDING, "degenerative_imaging"),
    ])
    branch = next(b for b in result.branches if b.causal_domain == "degenerative")
    assert branch.description.endswith("not a diagnosis.")
    assert "imaging_explains_symptoms_automatically" in result.prohibited_conclusions


def test_normal_or_absent_imaging_does_not_remove_functional_branch():
    result = HipComplexExpansionEngine().expand("HIP-003", [
        fact("f1", BiomechanicalFactKind.MOVEMENT_PATTERN, "gait_asymmetry"),
        fact("f2", BiomechanicalFactKind.CONTEXT, "normal_imaging"),
    ])
    assert any(b.causal_domain == "biomechanical_load" for b in result.branches)
    assert "normal_imaging_excludes_functional_mechanism" in result.prohibited_conclusions


def test_safety_critical_branch_is_unsafe_to_close():
    result = HipComplexExpansionEngine().expand("HIP-004", [
        fact("f1", BiomechanicalFactKind.SYMPTOM, "radiating_leg_pain"),
        fact("f2", BiomechanicalFactKind.PHYSICAL_FINDING, "neurological_deficit"),
    ])
    branch = next(b for b in result.branches if b.causal_domain == "lumbar_radicular")
    assert branch.safety_critical is True
    assert branch.status == BranchStatus.UNSAFE_TO_CLOSE
    assert branch.id in result.red_flag_branch_ids


def test_trauma_branch_retains_fracture_screen_as_missing_evidence():
    result = HipComplexExpansionEngine().expand("HIP-005", [
        fact("f1", BiomechanicalFactKind.TRAUMA_HISTORY, "recent_fall"),
        fact("f2", BiomechanicalFactKind.FUNCTIONAL_LIMITATION, "inability_to_weight_bear"),
    ])
    branch = next(b for b in result.branches if b.causal_domain == "traumatic")
    assert any("fracture_screen" in item for item in branch.missing_evidence_ids)


def test_postoperative_context_creates_separate_branch():
    result = HipComplexExpansionEngine().expand("HIP-006", [
        fact("f1", BiomechanicalFactKind.PROCEDURE_HISTORY, "recent_procedure"),
        fact("f2", BiomechanicalFactKind.PROCEDURE_HISTORY, "implant_present"),
    ])
    assert any(b.causal_domain == "iatrogenic_or_postoperative" for b in result.branches)


def test_referred_pain_remains_independent_from_local_joint_branch():
    result = HipComplexExpansionEngine().expand("HIP-007", [
        fact("f1", BiomechanicalFactKind.SYMPTOM, "groin_pain"),
        fact("f2", BiomechanicalFactKind.PHYSICAL_FINDING, "pain_not_reproduced_at_hip"),
    ])
    domains = {b.causal_domain for b in result.branches}
    assert "local_joint" in domains and "referred_pain" in domains


def test_unassigned_facts_are_preserved_not_discarded():
    result = HipComplexExpansionEngine().expand("HIP-008", [
        fact("f1", BiomechanicalFactKind.CONTEXT, "unknown_context_fact"),
        fact("f2", BiomechanicalFactKind.SYMPTOM, "groin_pain"),
    ])
    assert result.unassigned_fact_ids == ["f1"]


def test_relationships_do_not_flatten_branches():
    result = HipComplexExpansionEngine().expand("HIP-009", [
        fact("f1", BiomechanicalFactKind.SYMPTOM, "groin_pain"),
        fact("f2", BiomechanicalFactKind.LOAD_EXPOSURE, "occupational_load"),
    ])
    branch_ids = {b.id for b in result.branches}
    assert len(branch_ids) == 2
    assert all(r.source_branch_id in branch_ids and r.target_branch_id in branch_ids for r in result.relationships)


def test_fact_requires_provenance():
    try:
        BiomechanicalFact("f", BiomechanicalFactKind.SYMPTOM, "groin_pain", True)
    except ValueError as exc:
        assert "provenance" in str(exc)
    else:
        raise AssertionError("expected provenance validation")


def test_vascular_red_flags_create_safety_branch():
    result = HipComplexExpansionEngine().expand("HIP-010", [
        fact("f1", BiomechanicalFactKind.RED_FLAG, "limb_swelling"),
        fact("f2", BiomechanicalFactKind.PHYSICAL_FINDING, "color_change"),
    ])
    branch = next(b for b in result.branches if b.causal_domain == "vascular")
    assert branch.safety_critical


def test_pain_severity_not_equated_with_tissue_damage():
    result = HipComplexExpansionEngine().expand("HIP-011", [
        fact("f1", BiomechanicalFactKind.SYMPTOM, "groin_pain", "severe"),
    ])
    assert "pain_severity_equals_tissue_damage" in result.prohibited_conclusions
