import pytest

from app.modules.clinical_reasoning.domain.causality import ProvenanceReference
from app.modules.clinical_reasoning.domain.dynamic_consilium import (
    BranchReview,
    ConsiliumRole,
    DynamicConsiliumEngine,
    ReviewPosition,
)
from app.modules.clinical_reasoning.domain.hypothesis_expansion import HypothesisBranch


PROV = [ProvenanceReference("FHOS_CURATED:S08E11", "1")]


def branch(branch_id: str, domain: str, safety: bool = False) -> HypothesisBranch:
    return HypothesisBranch(
        id=branch_id,
        case_id="TEST-001",
        title=branch_id,
        description="candidate branch",
        root_trigger_ids=[f"fact:{branch_id}"],
        causal_domain=domain,
        branch_type="primary_mechanistic",
        node_ids=[f"fact:{branch_id}", f"mechanism:{branch_id}"],
        edge_ids=[f"edge:{branch_id}"],
        provenance=PROV,
        safety_critical=safety,
    )


def review(role: str, branch_id: str, position: ReviewPosition, *, requested=None) -> BranchReview:
    return BranchReview(
        role_code=role,
        branch_id=branch_id,
        position=position,
        rationale="structured review",
        requested_evidence_ids=requested or [],
        confidence=0.6,
        provenance=PROV,
    )


def roles():
    return [
        ConsiliumRole("endocrinology", "Endocrinology", ["glycemic_regulation"]),
        ConsiliumRole("cardiology", "Cardiology", ["lipid_metabolism"]),
        ConsiliumRole("devil", "Devil Review", devil_role=True),
    ]


def test_review_requires_provenance():
    with pytest.raises(ValueError):
        BranchReview("devil", "b1", ReviewPosition.NEUTRAL, "x", provenance=[])


def test_consilium_preserves_all_reviewed_branches():
    branches = [branch("b1", "glycemic_regulation"), branch("b2", "lipid_metabolism")]
    result = DynamicConsiliumEngine().evaluate(
        "TEST-001",
        branches,
        roles(),
        [review("endocrinology", "b1", ReviewPosition.SUPPORTS), review("cardiology", "b2", ReviewPosition.SUPPORTS)],
    )
    assert result.consensus.retained_branch_ids == ["b1", "b2"]
    assert not any(v.code == "consilium_flattened_graph" for v in result.violations)


def test_branch_without_review_is_violation():
    branches = [branch("b1", "glycemic_regulation"), branch("b2", "renal_filtration")]
    result = DynamicConsiliumEngine().evaluate("TEST-001", branches, roles(), [review("devil", "b1", ReviewPosition.NEUTRAL)])
    assert any(v.code == "branch_without_review" and v.branch_ids == ["b2"] for v in result.violations)


def test_minority_opinion_remains_visible():
    branches = [branch("b1", "glycemic_regulation")]
    result = DynamicConsiliumEngine().evaluate(
        "TEST-001",
        branches,
        roles(),
        [
            review("endocrinology", "b1", ReviewPosition.SUPPORTS),
            review("cardiology", "b1", ReviewPosition.SUPPORTS),
            review("devil", "b1", ReviewPosition.WEAKENS),
        ],
    )
    assert len(result.consensus.minority_opinions) == 1
    assert result.consensus.minority_opinions[0].role_code == "devil"


def test_consensus_does_not_claim_diagnosis():
    result = DynamicConsiliumEngine().evaluate(
        "TEST-001",
        [branch("b1", "glycemic_regulation")],
        roles(),
        [review("endocrinology", "b1", ReviewPosition.SUPPORTS)],
    )
    assert "diagnosis_confirmed" in result.consensus.prohibited_conclusions
    assert "does not establish diagnosis" in result.consensus.summary


def test_safety_branch_is_unsafe_to_close():
    result = DynamicConsiliumEngine().evaluate(
        "TEST-001",
        [branch("b1", "vascular", safety=True)],
        roles(),
        [review("devil", "b1", ReviewPosition.SAFETY_HOLD)],
    )
    assert result.consensus.unsafe_to_close_branch_ids == ["b1"]


def test_requested_evidence_is_aggregated():
    result = DynamicConsiliumEngine().evaluate(
        "TEST-001",
        [branch("b1", "hepatic_integrity")],
        roles(),
        [review("devil", "b1", ReviewPosition.REQUESTS_EVIDENCE, requested=["timeline", "repeat_alt"])],
    )
    assert result.consensus.missing_evidence_ids == ["repeat_alt", "timeline"]


def test_cluster_cannot_replace_member_branch():
    branches = [branch("b1", "glycemic_regulation"), branch("b2", "lipid_metabolism")]
    result = DynamicConsiliumEngine().evaluate(
        "TEST-001",
        branches,
        roles(),
        [review("endocrinology", "b1", ReviewPosition.SUPPORTS)],
        [["b1", "b2"]],
    )
    assert any(v.code == "cluster_replaced_member_branches" and v.branch_ids == ["b2"] for v in result.violations)


def test_missing_devil_role_is_warning_not_violation():
    result = DynamicConsiliumEngine().evaluate(
        "TEST-001",
        [branch("b1", "renal_filtration")],
        [ConsiliumRole("nephrology", "Nephrology")],
        [review("nephrology", "b1", ReviewPosition.NEUTRAL)],
    )
    assert "devil_role_missing" in result.warnings
    assert all(v.code != "devil_role_missing" for v in result.violations)


def test_unknown_review_references_are_warnings():
    result = DynamicConsiliumEngine().evaluate(
        "TEST-001",
        [branch("b1", "renal_filtration")],
        roles(),
        [review("unknown", "b1", ReviewPosition.NEUTRAL), review("devil", "missing", ReviewPosition.NEUTRAL)],
    )
    assert "review_references_unknown_role:unknown" in result.warnings
    assert "review_references_unknown_branch:missing" in result.warnings


def test_two_supports_can_mark_branch_leading_without_closing_others():
    branches = [branch("b1", "glycemic_regulation"), branch("b2", "hepatic_integrity")]
    result = DynamicConsiliumEngine().evaluate(
        "TEST-001",
        branches,
        roles(),
        [
            review("endocrinology", "b1", ReviewPosition.SUPPORTS),
            review("cardiology", "b1", ReviewPosition.SUPPORTS),
            review("devil", "b2", ReviewPosition.NEUTRAL),
        ],
    )
    assert result.consensus.leading_branch_ids == ["b1"]
    assert "b2" in result.consensus.retained_branch_ids
    assert "b2" in result.consensus.unresolved_branch_ids
