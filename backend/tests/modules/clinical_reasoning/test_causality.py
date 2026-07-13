from app.modules.clinical_reasoning.domain.causality import (
    CausalityRelation,
    CausalityRelationKind,
    MechanismStatus,
    build_causality_assessment,
)
from app.modules.clinical_reasoning.domain.laboratory_profile import (
    EvidenceRole,
    ObservationClass,
    LaboratoryObservationSnapshot,
)


def observation(result_id: int, code: str, value: float, interpretation: str):
    return LaboratoryObservationSnapshot(
        laboratory_result_id=result_id,
        patient_id="TEST-001",
        episode_id="EP-1",
        node_id=f"LAB:{code}",
        test_code=code,
        test_name=code,
        value=value,
        unit=None,
        reference_min=None,
        reference_max=None,
        critical_low=None,
        critical_high=None,
        interpretation=interpretation,
        observation_class=(
            ObservationClass.OUTSIDE_REFERENCE
            if interpretation != "normal"
            else ObservationClass.WITHIN_REFERENCE
        ),
        evidence_role=(
            EvidenceRole.SIGNAL
            if interpretation != "normal"
            else EvidenceRole.CONTEXT
        ),
        result_date=None,
        provenance={"type": "laboratory_result", "laboratory_result_id": result_id},
    )


def test_causality_relation_requires_valid_confidence():
    relation = CausalityRelation(
        from_code="fact",
        to_code="process",
        relation_kind=CausalityRelationKind.INDICATES_PROCESS,
        status=MechanismStatus.PLAUSIBLE,
        confidence=0.5,
        rationale="test",
        source_key="FHOS_CURATED:S08E06",
    )
    assert relation.confidence == 0.5


def test_full_profile_builds_four_clinical_branches_and_preserves_all_facts():
    observations = [
        observation(1, "GLUCOSE_FASTING", 7.4, "high"),
        observation(2, "HBA1C", 6.8, "high"),
        observation(3, "INSULIN_FASTING", 18.0, "normal"),
        observation(4, "ALT", 52.0, "high"),
        observation(5, "TRIGLYCERIDES", 2.3, "high"),
        observation(6, "CREATININE", 88.0, "normal"),
    ]
    result = build_causality_assessment("TEST-001", "EP-1", observations)

    assert {branch.code for branch in result.branches} == {
        "glycemic_regulation",
        "lipid_metabolism",
        "hepatic_integrity",
        "renal_filtration",
    }
    assert result.unassigned_fact_ids == []
    assert result.devil_review["passed"] is True
    assert result.devil_review["checks"]["all_observations_preserved"] is True


def test_normal_creatinine_is_kept_in_renal_branch_and_does_not_prove_health():
    result = build_causality_assessment(
        "TEST-001",
        "EP-1",
        [observation(6, "CREATININE", 88.0, "normal")],
    )
    branch = result.branches[0]
    statuses = {item["code"]: item["status"] for item in branch.mechanisms}

    assert branch.patient_fact_ids == ["laboratory_result:6"]
    assert statuses["reduced_glomerular_filtration"] == "contradicted"
    assert "kidneys_healthy" in branch.prohibited_conclusions
    assert "eGFR" in branch.missing_evidence


def test_unknown_observation_is_preserved_as_unassigned_fact():
    result = build_causality_assessment(
        "TEST-001",
        "EP-1",
        [observation(7, "UNKNOWN_TEST", 1.0, "normal")],
    )
    assert result.branches == []
    assert result.unassigned_fact_ids == ["laboratory_result:7"]
    assert result.devil_review["passed"] is False
