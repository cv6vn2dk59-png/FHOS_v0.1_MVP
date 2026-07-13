from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from itertools import combinations
from typing import Iterable

from .causality import ProvenanceReference
from .hypothesis_expansion import HypothesisBranch


class EvidenceEffectType(str, Enum):
    SUPPORTS = "supports"
    WEAKENS = "weakens"
    CONTRADICTS = "contradicts"
    DOES_NOT_DISCRIMINATE = "does_not_discriminate"
    CHANGES_URGENCY = "changes_urgency"
    CHANGES_CONTEXT = "changes_context"


@dataclass(frozen=True)
class BranchEvidenceEffect:
    branch_id: str
    possible_result: str
    effect_type: EvidenceEffectType
    expected_strength: float

    def __post_init__(self) -> None:
        if not 0 <= self.expected_strength <= 1:
            raise ValueError("expected_strength must be between 0 and 1")
        if not self.possible_result.strip():
            raise ValueError("possible_result is required")


@dataclass
class EvidenceCandidate:
    id: str
    proposed_data_item: str
    evidence_type: str
    affected_branch_ids: list[str]
    effects: list[BranchEvidenceEffect]
    evidence_reliability: float
    context_applicability: float
    clinical_utility: float
    safety_priority: float
    time_sensitivity: float
    invasiveness: float
    cost_burden: float
    actionability: float
    provenance: list[ProvenanceReference]
    limitations: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.proposed_data_item.strip():
            raise ValueError("proposed_data_item is required")
        if not self.provenance:
            raise ValueError("evidence candidate requires provenance")
        for name in (
            "evidence_reliability",
            "context_applicability",
            "clinical_utility",
            "safety_priority",
            "time_sensitivity",
            "invasiveness",
            "cost_burden",
            "actionability",
        ):
            value = getattr(self, name)
            if not 0 <= value <= 1:
                raise ValueError(f"{name} must be between 0 and 1")
        effect_branch_ids = {effect.branch_id for effect in self.effects}
        if not effect_branch_ids.issubset(set(self.affected_branch_ids)):
            raise ValueError("effect branch must be listed in affected_branch_ids")


@dataclass(frozen=True)
class BranchComparison:
    branch_a_id: str
    branch_b_id: str
    shared_fact_ids: list[str]
    differentiating_fact_ids: list[str]
    conflicting_fact_ids: list[str]
    missing_discriminator_ids: list[str]
    relationship_type: str
    comparison_summary: str
    evidence_support_separation: float
    mechanistic_separation: float
    temporal_separation: float
    safety_importance: float


@dataclass(frozen=True)
class RankedEvidenceCandidate:
    candidate_id: str
    information_gain: float
    priority_score: float
    branch_separation: float
    affected_branch_ids: list[str]
    rationale: str


@dataclass
class BranchDiscriminationResult:
    case_id: str
    comparisons: list[BranchComparison]
    ranked_candidates: list[RankedEvidenceCandidate]
    unresolved_branch_pairs: list[tuple[str, str]]
    limitations: list[str]
    warnings: list[str]


class BranchDiscriminationEngine:
    """Ranks missing evidence by discrimination value, not by diagnostic certainty.

    Scores are decision-support heuristics. They are intentionally separate from
    clinical risk and must never be presented as probability of disease.
    """

    def compare(self, left: HypothesisBranch, right: HypothesisBranch) -> BranchComparison:
        if left.id == right.id:
            raise ValueError("cannot compare a branch with itself")

        left_facts = set(left.supporting_fact_ids + left.neutral_fact_ids + left.contradicting_fact_ids)
        right_facts = set(right.supporting_fact_ids + right.neutral_fact_ids + right.contradicting_fact_ids)
        shared = sorted(left_facts & right_facts)
        differentiating = sorted(left_facts ^ right_facts)
        conflicts = sorted(
            (set(left.supporting_fact_ids) & set(right.contradicting_fact_ids))
            | (set(right.supporting_fact_ids) & set(left.contradicting_fact_ids))
        )
        missing = sorted(set(left.missing_evidence_ids) | set(right.missing_evidence_ids))

        same_domain = left.causal_domain == right.causal_domain
        relationship = "competing" if shared else "parallel_or_independent"
        if same_domain:
            relationship = "same_domain_alternative"

        support_separation = self._bounded(
            (len(differentiating) + 2 * len(conflicts)) / max(1, len(left_facts | right_facts))
        )
        mechanistic_separation = self._bounded(
            0.0 if left.node_ids == right.node_ids else 1 - self._jaccard(left.node_ids, right.node_ids)
        )
        temporal_separation = 0.5 if any("time" in item.lower() or "repeat" in item.lower() for item in missing) else 0.0
        safety_importance = max(float(left.safety_critical), float(right.safety_critical))

        return BranchComparison(
            branch_a_id=left.id,
            branch_b_id=right.id,
            shared_fact_ids=shared,
            differentiating_fact_ids=differentiating,
            conflicting_fact_ids=conflicts,
            missing_discriminator_ids=missing,
            relationship_type=relationship,
            comparison_summary="Branches remain separately testable; comparison does not select a diagnosis.",
            evidence_support_separation=support_separation,
            mechanistic_separation=mechanistic_separation,
            temporal_separation=temporal_separation,
            safety_importance=safety_importance,
        )

    def evaluate(
        self,
        case_id: str,
        branches: Iterable[HypothesisBranch],
        candidates: Iterable[EvidenceCandidate],
    ) -> BranchDiscriminationResult:
        branch_list = list(branches)
        candidate_list = list(candidates)
        branch_ids = {branch.id for branch in branch_list}
        if len(branch_list) < 2:
            return BranchDiscriminationResult(
                case_id=case_id,
                comparisons=[],
                ranked_candidates=[],
                unresolved_branch_pairs=[],
                limitations=["At least two branches are required for discrimination."],
                warnings=["single_branch_without_comparison"],
            )

        comparisons = [self.compare(left, right) for left, right in combinations(branch_list, 2)]
        valid_candidates = [c for c in candidate_list if set(c.affected_branch_ids).issubset(branch_ids)]
        warnings: list[str] = []
        if len(valid_candidates) != len(candidate_list):
            warnings.append("candidate_references_unknown_branch")

        ranked = sorted(
            (self._rank(candidate, comparisons, branch_list) for candidate in valid_candidates),
            key=lambda item: (item.priority_score, item.information_gain, item.candidate_id),
            reverse=True,
        )

        covered_pairs: set[tuple[str, str]] = set()
        for candidate in valid_candidates:
            discriminating_ids = {
                effect.branch_id
                for effect in candidate.effects
                if effect.effect_type != EvidenceEffectType.DOES_NOT_DISCRIMINATE
                and effect.expected_strength > 0
            }
            for left_id, right_id in combinations(sorted(discriminating_ids), 2):
                left_effects = [e for e in candidate.effects if e.branch_id == left_id]
                right_effects = [e for e in candidate.effects if e.branch_id == right_id]
                if self._effects_separate(left_effects, right_effects):
                    covered_pairs.add((left_id, right_id))

        all_pairs = {(min(c.branch_a_id, c.branch_b_id), max(c.branch_a_id, c.branch_b_id)) for c in comparisons}
        unresolved = sorted(all_pairs - covered_pairs)
        limitations = []
        if unresolved:
            limitations.append("Some branch pairs have no evidence candidate with a separating expected effect.")
        if not valid_candidates:
            limitations.append("No valid evidence candidates were supplied.")

        return BranchDiscriminationResult(
            case_id=case_id,
            comparisons=comparisons,
            ranked_candidates=ranked,
            unresolved_branch_pairs=unresolved,
            limitations=limitations,
            warnings=warnings,
        )

    def _rank(
        self,
        candidate: EvidenceCandidate,
        comparisons: list[BranchComparison],
        branches: list[HypothesisBranch],
    ) -> RankedEvidenceCandidate:
        separation = self._candidate_separation(candidate)
        information_gain = self._bounded(
            separation
            * candidate.evidence_reliability
            * candidate.context_applicability
            * candidate.actionability
        )
        safety_branch_bonus = max(
            (1.0 if branch.safety_critical and branch.id in candidate.affected_branch_ids else 0.0)
            for branch in branches
        )
        benefit = (
            0.45 * information_gain
            + 0.20 * candidate.clinical_utility
            + 0.15 * max(candidate.safety_priority, safety_branch_bonus)
            + 0.10 * candidate.time_sensitivity
            + 0.10 * candidate.actionability
        )
        burden = 0.10 * candidate.invasiveness + 0.08 * candidate.cost_burden
        priority = self._bounded(benefit - burden)
        rationale = (
            "Priority reflects branch separation, reliability, clinical utility, safety, timing and burden; "
            "it is not a disease probability or clinical risk score."
        )
        return RankedEvidenceCandidate(
            candidate_id=candidate.id,
            information_gain=round(information_gain, 6),
            priority_score=round(priority, 6),
            branch_separation=round(separation, 6),
            affected_branch_ids=list(candidate.affected_branch_ids),
            rationale=rationale,
        )

    def _candidate_separation(self, candidate: EvidenceCandidate) -> float:
        by_branch: dict[str, list[BranchEvidenceEffect]] = {}
        for effect in candidate.effects:
            by_branch.setdefault(effect.branch_id, []).append(effect)
        pair_scores: list[float] = []
        for left_id, right_id in combinations(sorted(by_branch), 2):
            left = by_branch[left_id]
            right = by_branch[right_id]
            if not self._effects_separate(left, right):
                pair_scores.append(0.0)
                continue
            left_strength = max(e.expected_strength for e in left)
            right_strength = max(e.expected_strength for e in right)
            pair_scores.append((left_strength + right_strength) / 2)
        return self._bounded(sum(pair_scores) / len(pair_scores)) if pair_scores else 0.0

    @staticmethod
    def _effects_separate(left: list[BranchEvidenceEffect], right: list[BranchEvidenceEffect]) -> bool:
        left_types = {e.effect_type for e in left}
        right_types = {e.effect_type for e in right}
        if left_types == {EvidenceEffectType.DOES_NOT_DISCRIMINATE}:
            return False
        if right_types == {EvidenceEffectType.DOES_NOT_DISCRIMINATE}:
            return False
        return left_types != right_types

    @staticmethod
    def _jaccard(left: Iterable[str], right: Iterable[str]) -> float:
        left_set, right_set = set(left), set(right)
        union = left_set | right_set
        return len(left_set & right_set) / len(union) if union else 1.0

    @staticmethod
    def _bounded(value: float) -> float:
        return min(1.0, max(0.0, value))
