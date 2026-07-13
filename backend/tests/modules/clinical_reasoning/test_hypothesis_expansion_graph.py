from app.modules.clinical_reasoning.domain.causality import CausalPath, ProvenanceReference
from app.modules.clinical_reasoning.domain.hypothesis_expansion import (
    BranchExpansionEngine, BranchStatus, DominanceGuard, HypothesisBranch,
)


def p(source="test"):
    return [ProvenanceReference(source, "1")]


def path(pid, domain, nodes):
    return CausalPath(pid, nodes, [f"{pid}:e{i}" for i in range(len(nodes)-1)], domain, p(pid))


def test_builds_multiple_independent_branches_from_same_fact():
    result = BranchExpansionEngine().expand("TEST-001", [
        path("g", "glycemic_regulation", ["fact:glucose", "process:glycemic", "mechanism:insulin", "missing:hba1c"]),
        path("e", "endocrine", ["fact:glucose", "process:endocrine", "mechanism:cortisol", "missing:timeline"]),
    ])
    assert len(result.branches) == 2
    assert {b.causal_domain for b in result.branches} == {"glycemic_regulation", "endocrine"}
    assert not result.violations


def test_cardiometabolic_cluster_does_not_replace_member_branches():
    result = BranchExpansionEngine().expand("TEST-001", [
        path("g", "glycemic_regulation", ["fact:g", "process:g", "mechanism:g"]),
        path("l", "lipid_metabolism", ["fact:l", "process:l", "mechanism:l"]),
        path("h", "hepatic_integrity", ["fact:h", "process:h", "mechanism:h"]),
        path("r", "renal_filtration", ["fact:r", "process:r", "mechanism:r"]),
    ])
    assert len(result.branches) == 4
    assert len(result.clusters) == 1
    assert len(result.clusters[0].branch_ids) == 3
    assert any(b.causal_domain == "renal_filtration" for b in result.branches)


def test_generates_discriminating_evidence_for_multiple_branches():
    result = BranchExpansionEngine().expand("X", [
        path("a", "metabolic", ["f", "m1"]), path("b", "iatrogenic", ["f", "m2"]),
    ])
    assert result.discriminators
    assert result.discriminators[0].information_gain > 0


def test_single_branch_is_flagged_not_silently_treated_as_complete():
    result = BranchExpansionEngine().expand("X", [path("a", "metabolic", ["f", "m"])] )
    assert "single_branch_without_alternatives" in result.violations


def test_closed_branch_without_contradiction_is_rejected_by_guard():
    branch = HypothesisBranch(
        id="b", case_id="c", title="t", description="candidate", root_trigger_ids=["f"],
        causal_domain="metabolic", branch_type="primary_mechanistic", node_ids=["f", "m"], edge_ids=["e"],
        status=BranchStatus.CLOSED, provenance=p(),
    )
    assert "branch_closed_without_evidence:b" in DominanceGuard().evaluate([branch])
