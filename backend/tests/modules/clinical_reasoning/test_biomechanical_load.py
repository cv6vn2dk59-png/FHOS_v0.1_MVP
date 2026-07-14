from app.modules.clinical_reasoning.domain.biomechanical_load import (
    AdaptationState, BiomechanicalLoadEngine, LoadEvidenceEffectType, LoadExposure, LoadExposureKind,
    LoadResponseObservation, OverloadPattern, RecoveryCapacity,
)
from app.modules.clinical_reasoning.domain.causality import ProvenanceReference
from app.modules.clinical_reasoning.domain.hypothesis_expansion import BranchStatus, HypothesisBranch

PROV=[ProvenanceReference("patient_history","S08E14","TEST-LOAD")]

def branch(domain="biomechanical_load"):
    return HypothesisBranch(id=f"b:{domain}",case_id="CASE",title=domain,description="candidate",root_trigger_ids=["f"],causal_domain=domain,branch_type="alternative_mechanistic",node_ids=["f","m"],edge_ids=["e"],evidence_strength="plausible",confidence=.5,status=BranchStatus.ACTIVE,provenance=PROV)

def exposure(kind=LoadExposureKind.TRAINING, magnitude=.9, id_="x1", freq=6):
    return LoadExposure(id_,kind,"load",magnitude=magnitude,duration_minutes=90,frequency_per_week=freq,provenance=PROV)

def recovery(current=.4, baseline=.8, hours=8):
    return RecoveryCapacity("r1",sleep_quality=.4,recovery_hours=hours,baseline_capacity=baseline,current_capacity=current,limiting_factors=("sleep_debt",),provenance=PROV)

def response(change=3, repeated=True):
    return LoadResponseObservation("lr1","x1",symptom_change=change,recovery_time_hours=36,repeated_pattern=repeated,provenance=PROV)

def test_capacity_demand_mismatch_supports_load_branch_without_proving_injury():
    result=BiomechanicalLoadEngine().evaluate("CASE",[branch()],[exposure()],recovery(),[response()])
    assert result.mismatches[0].mismatch>0
    assert any(e.effect_type==LoadEvidenceEffectType.SUPPORTS for e in result.effects)
    assert "high_load_equals_injury" in result.prohibited_conclusions

def test_acute_spike_kept_separate_from_chronic_exposure():
    result=BiomechanicalLoadEngine().evaluate("CASE",[branch()],[exposure(LoadExposureKind.ACUTE_EVENT)],recovery(),[response()])
    patterns=result.branch_assessments[0].overload_patterns
    assert OverloadPattern.ACUTE_SPIKE in patterns
    assert OverloadPattern.CHRONIC_EXCESS not in patterns

def test_repetitive_occupational_exposure_is_context_not_diagnosis():
    result=BiomechanicalLoadEngine().evaluate("CASE",[branch("degenerative")],[exposure(LoadExposureKind.OCCUPATIONAL)],recovery(),[response()])
    assert OverloadPattern.REPETITIVE_EXPOSURE in result.branch_assessments[0].overload_patterns
    assert any(e.effect_type==LoadEvidenceEffectType.CHANGES_CONTEXT for e in result.effects)

def test_recovery_deficit_may_amplify_but_not_prove_causality():
    result=BiomechanicalLoadEngine().evaluate("CASE",[branch()],[exposure()],recovery(),[response()])
    assert OverloadPattern.RECOVERY_DEFICIT in result.branch_assessments[0].overload_patterns
    assert "recovery_deficit_proves_causality" in result.prohibited_conclusions

def test_reduced_capacity_can_coexist_with_no_structural_claim():
    result=BiomechanicalLoadEngine().evaluate("CASE",[branch()],[exposure()],recovery(current=.2),[response()])
    assert result.mismatches[0].mismatch>0
    assert "low_capacity_equals_structural_pathology" in result.prohibited_conclusions

def test_missing_recovery_is_missing_evidence_not_negative():
    result=BiomechanicalLoadEngine().evaluate("CASE",[branch()],[exposure()],None,[response()])
    assert any(m.required_item=="recovery_capacity" for m in result.missing_evidence)
    assert result.branch_assessments[0].weakening_evidence_ids==[]

def test_missing_load_response_is_explicit():
    result=BiomechanicalLoadEngine().evaluate("CASE",[branch()],[exposure()],recovery(),[])
    assert any(m.required_item=="load_response_observation" for m in result.missing_evidence)
    assert result.branch_assessments[0].adaptation_state==AdaptationState.UNKNOWN

def test_improving_response_can_indicate_positive_adaptation():
    result=BiomechanicalLoadEngine().evaluate("CASE",[branch()],[exposure(magnitude=.2,freq=2)],RecoveryCapacity("r",sleep_quality=.9,current_capacity=.9,baseline_capacity=.8,recovery_hours=24,provenance=PROV),[response(change=-2)])
    assert result.branch_assessments[0].adaptation_state==AdaptationState.POSITIVE

def test_high_load_without_symptom_pattern_does_not_confirm_overload():
    result=BiomechanicalLoadEngine().evaluate("CASE",[branch()],[exposure()],recovery(current=.95,baseline=.95,hours=24),[])
    assert OverloadPattern.CHRONIC_EXCESS not in result.branch_assessments[0].overload_patterns

def test_non_load_domain_preserved_without_forced_assignment():
    result=BiomechanicalLoadEngine().evaluate("CASE",[branch("vascular")],[exposure()],recovery(),[response()])
    assert result.branch_assessments[0].adaptation_state==AdaptationState.UNKNOWN
    assert result.unassigned_exposure_ids==["x1"]

def test_load_exposure_requires_provenance():
    try: LoadExposure("x",LoadExposureKind.TRAINING,"load")
    except ValueError as exc: assert "provenance" in str(exc)
    else: raise AssertionError("expected provenance validation")

def test_negative_values_rejected():
    try: LoadExposure("x",LoadExposureKind.TRAINING,"load",magnitude=-1,provenance=PROV)
    except ValueError as exc: assert "negative" in str(exc)
    else: raise AssertionError("expected validation")
