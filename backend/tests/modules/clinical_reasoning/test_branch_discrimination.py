import pytest

from app.modules.clinical_reasoning.domain.branch_discrimination import (
    BranchDiscriminationEngine,
    BranchEvidenceEffect,
    EvidenceCandidate,
    EvidenceEffectType,
)
from app.modules.clinical_reasoning.domain.causality import ProvenanceReference
from app.modules.clinical_reasoning.domain.hypothesis_expansion import HypothesisBranch


def provenance():
    return [ProvenanceReference("FHOS_CURATED:S08E08", "1")]


def branch(branch_id, domain, *, supporting=None, contradicting=None, missing=None, safety=False):
    return HypothesisBranch(
        id=branch_id,
        case_id="TEST-001",
        title=domain,
        description="Candidate mechanism; not a diagnosis.",
        root_trigger_ids=["fact:root"],
        causal_domain=domain,
        branch_type="alternative_mechanistic",
        node_ids=["fact:root", f"mechanism:{domain}"],
        edge_ids=[f"edge:{domain}"],
        supporting_fact_ids=supporting or [],
        contradicting_fact_ids=contradicting or [],
        missing_evidence_ids=missing or [],
        provenance=provenance(),
        safety_critical=safety,
    )


def candidate(candidate_id, effects, **overrides):
    values = dict(
        proposed_data_item="Repeat measurement in a controlled clinical context",
        evidence_type="laboratory_or_timeline",
        affected_branch_ids=sorted({effect.branch_id for effect in effects}),
        effects=effects,
        evidence_reliability=0.9,
        context_applicability=0.9,
        clinical_utility=0.8,
        safety_priority=0.4,
        time_sensitivity=0.5,
        invasiveness=0.1,
        cost_burden=0.1,
        actionability=0.8,
        provenance=provenance(),
    )
    values.update(overrides)
    return EvidenceCandidate(id=candidate_id, **values)


def effect(branch_id, effect_type, strength=0.8):
    return BranchEvidenceEffect(branch_id, "possible result", effect_type, strength)


def test_compares_each_branch_pair_without_selecting_a_diagnosis():
    branches = [branch("g", "glycemic"), branch("h", "hepatic"), branch("r", "renal")]
    result = BranchDiscriminationEngine().evaluate("TEST-001", branches, [])
    assert len(result.comparisons) == 3
    assert all("does not select a diagnosis" in c.comparison_summary for c in result.comparisons)


def test_shared_and_conflicting_evidence_are_separate_dimensions():
    left = branch("a", "metabolic", supporting=["fact:1", "fact:2"])
    right = branch("b", "endocrine", supporting=["fact:1"], contradicting=["fact:2"])
    comparison = BranchDiscriminationEngine().compare(left, right)
    assert comparison.shared_fact_ids == ["fact:1", "fact:2"]
    assert comparison.conflicting_fact_ids == ["fact:2"]


def test_information_gain_depends_on_separation_not_only_utility():
    branches = [branch("a", "metabolic"), branch("b", "iatrogenic")]
    separating = candidate("separating", [effect("a", EvidenceEffectType.SUPPORTS), effect("b", EvidenceEffectType.WEAKENS)])
    nondiscriminating = candidate(
        "nondiscriminating",
        [effect("a", EvidenceEffectType.SUPPORTS), effect("b", EvidenceEffectType.SUPPORTS)],
        clinical_utility=1.0,
    )
    result = BranchDiscriminationEngine().evaluate("TEST-001", branches, [separating, nondiscriminating])
    scores = {item.candidate_id: item.information_gain for item in result.ranked_candidates}
    assert scores["separating"] > scores["nondiscriminating"]
    assert scores["nondiscriminating"] == 0


def test_cost_and_invasiveness_reduce_priority_but_not_information_gain():
    branches = [branch("a", "metabolic"), branch("b", "iatrogenic")]
    effects = [effect("a", EvidenceEffectType.SUPPORTS), effect("b", EvidenceEffectType.CONTRADICTS)]
    low_burden = candidate("low", effects, invasiveness=0.0, cost_burden=0.0)
    high_burden = candidate("high", effects, invasiveness=1.0, cost_burden=1.0)
    result = BranchDiscriminationEngine().evaluate("TEST-001", branches, [low_burden, high_burden])
    ranked = {item.candidate_id: item for item in result.ranked_candidates}
    assert ranked["low"].information_gain == ranked["high"].information_gain
    assert ranked["low"].priority_score > ranked["high"].priority_score


def test_safety_critical_branch_increases_priority_without_forcing_diagnosis():
    branches = [branch("a", "common"), branch("b", "dangerous", safety=True)]
    item = candidate(
        "safety",
        [effect("a", EvidenceEffectType.WEAKENS), effect("b", EvidenceEffectType.CHANGES_URGENCY)],
        safety_priority=0.2,
    )
    result = BranchDiscriminationEngine().evaluate("TEST-001", branches, [item])
    assert result.ranked_candidates[0].priority_score > 0
    assert "risk score" in result.ranked_candidates[0].rationale


def test_unresolved_pairs_are_explicit():
    branches = [branch("a", "one"), branch("b", "two"), branch("c", "three")]
    item = candidate("ab", [effect("a", EvidenceEffectType.SUPPORTS), effect("b", EvidenceEffectType.WEAKENS)])
    result = BranchDiscriminationEngine().evaluate("TEST-001", branches, [item])
    assert ("a", "c") in result.unresolved_branch_pairs
    assert ("b", "c") in result.unresolved_branch_pairs


def test_unknown_branch_candidate_is_warned_and_not_ranked():
    branches = [branch("a", "one"), branch("b", "two")]
    item = candidate("bad", [effect("a", EvidenceEffectType.SUPPORTS), effect("x", EvidenceEffectType.WEAKENS)])
    result = BranchDiscriminationEngine().evaluate("TEST-001", branches, [item])
    assert result.ranked_candidates == []
    assert "candidate_references_unknown_branch" in result.warnings


def test_candidate_requires_provenance():
    with pytest.raises(ValueError, match="requires provenance"):
        EvidenceCandidate(
            id="x", proposed_data_item="x", evidence_type="question", affected_branch_ids=[], effects=[],
            evidence_reliability=1, context_applicability=1, clinical_utility=1, safety_priority=0,
            time_sensitivity=0, invasiveness=0, cost_burden=0, actionability=1, provenance=[],
        )


def test_candidate_scores_must_be_bounded():
    with pytest.raises(ValueError, match="cost_burden"):
        candidate("x", [], cost_burden=1.1)


def test_single_branch_is_not_ranked_as_discrimination():
    result = BranchDiscriminationEngine().evaluate("TEST-001", [branch("a", "one")], [])
    assert result.ranked_candidates == []
    assert "single_branch_without_comparison" in result.warnings
