from app.modules.clinical_reasoning.domain.causality import ContextConstraint, ProvenanceReference
from app.modules.clinical_reasoning.domain.hypothesis_expansion import HypothesisBranch
from app.modules.clinical_reasoning.domain.mechanistic_clustering import (
    BranchMechanisticProfile,
    ClusterConflictType,
    ClusterType,
    MechanisticClusteringEngine,
)


def prov():
    return [ProvenanceReference("FHOS_CURATED:S08E10", "1")]


def branch(branch_id, domain):
    return HypothesisBranch(
        id=branch_id,
        case_id="TEST-001",
        title=domain,
        description="candidate branch",
        root_trigger_ids=[f"fact:{branch_id}"],
        causal_domain=domain,
        branch_type="primary_mechanistic",
        node_ids=[f"fact:{branch_id}", f"mechanism:{branch_id}"],
        edge_ids=[f"edge:{branch_id}"],
        provenance=prov(),
    )


def profile(branch_id, systems, upstream=None, downstream=None, risks=None, constraints=None):
    return BranchMechanisticProfile(
        branch_id=branch_id,
        body_systems=systems,
        upstream_mechanism_ids=upstream or [],
        downstream_consequence_ids=downstream or [],
        risk_factor_ids=risks or [],
        provenance=prov(),
        context_constraints=constraints or [],
    )


def test_shared_upstream_mechanism_builds_cross_system_cluster():
    result = MechanisticClusteringEngine().cluster(
        "TEST-001",
        [branch("g", "glycemic"), branch("h", "hepatic")],
        [profile("g", ["endocrine"], upstream=["insulin_resistance"]), profile("h", ["hepatic"], upstream=["insulin_resistance"])],
    )
    assert len(result.clusters) == 1
    assert result.clusters[0].cluster_type == ClusterType.CROSS_SYSTEM_CLUSTER
    assert set(result.clusters[0].branch_ids) == {"g", "h"}


def test_cluster_preserves_member_branches():
    branches = [branch("a", "metabolic"), branch("b", "vascular")]
    result = MechanisticClusteringEngine().cluster(
        "TEST-001", branches,
        [profile("a", ["metabolic"], upstream=["m"]), profile("b", ["vascular"], upstream=["m"])],
    )
    assert result.branches == branches
    assert result.clusters[0].member_branches_preserved is True


def test_shared_consequence_does_not_become_shared_cause():
    result = MechanisticClusteringEngine().cluster(
        "TEST-001",
        [branch("a", "renal"), branch("b", "vascular")],
        [profile("a", ["renal"], downstream=["hypertension"]), profile("b", ["vascular"], downstream=["hypertension"])],
    )
    assert result.clusters[0].cluster_type == ClusterType.SHARED_DOWNSTREAM_CONSEQUENCE
    assert any(c.code == ClusterConflictType.SHARED_CONSEQUENCE_TREATED_AS_SHARED_CAUSE for c in result.conflicts)


def test_common_risk_factor_does_not_merge_mechanisms():
    result = MechanisticClusteringEngine().cluster(
        "TEST-001",
        [branch("a", "hepatic"), branch("b", "vascular")],
        [profile("a", ["hepatic"], risks=["smoking"]), profile("b", ["vascular"], risks=["smoking"])],
    )
    assert any(c.code == ClusterConflictType.SHARED_RISK_FACTOR_TREATED_AS_SINGLE_MECHANISM for c in result.conflicts)


def test_independent_branch_remains_visible():
    result = MechanisticClusteringEngine().cluster(
        "TEST-001",
        [branch("g", "glycemic"), branch("h", "hepatic"), branch("r", "renal")],
        [profile("g", ["endocrine"], upstream=["insulin_resistance"]), profile("h", ["hepatic"], upstream=["insulin_resistance"]), profile("r", ["renal"], upstream=["reduced_filtration"])],
    )
    assert result.independent_branch_ids == ["r"]


def test_unknown_profile_is_warning_not_crash():
    result = MechanisticClusteringEngine().cluster(
        "TEST-001", [branch("a", "metabolic")], [profile("missing", ["other"], upstream=["x"])],
    )
    assert "profile_references_unknown_branch:missing" in result.warnings


def test_no_overlap_returns_limitation():
    result = MechanisticClusteringEngine().cluster(
        "TEST-001",
        [branch("a", "a"), branch("b", "b")],
        [profile("a", ["a"], upstream=["x"]), profile("b", ["b"], upstream=["y"])],
    )
    assert not result.clusters
    assert any("No cross-system cluster" in item for item in result.limitations)


def test_profile_requires_provenance():
    try:
        BranchMechanisticProfile(branch_id="a", body_systems=["x"], provenance=[])
    except ValueError as exc:
        assert "provenance" in str(exc)
    else:
        raise AssertionError("missing provenance accepted")


def test_common_context_constraints_are_preserved():
    common = ContextConstraint("age", ">=", 18)
    result = MechanisticClusteringEngine().cluster(
        "TEST-001",
        [branch("a", "a"), branch("b", "b")],
        [profile("a", ["a"], upstream=["m"], constraints=[common]), profile("b", ["b"], upstream=["m"], constraints=[common])],
    )
    assert result.clusters[0].context_constraints == [common]


def test_cluster_output_has_non_diagnostic_limitations():
    result = MechanisticClusteringEngine().cluster(
        "TEST-001",
        [branch("a", "a"), branch("b", "b")],
        [profile("a", ["a"], upstream=["m"]), profile("b", ["b"], upstream=["m"])],
    )
    assert any("not diagnoses" in item for item in result.limitations)
