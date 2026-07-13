from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable

from .causality import ProvenanceReference
from .hypothesis_expansion import HypothesisBranch


class ReviewPosition(str, Enum):
    SUPPORTS = "supports"
    WEAKENS = "weakens"
    NEUTRAL = "neutral"
    REQUESTS_EVIDENCE = "requests_evidence"
    SAFETY_HOLD = "safety_hold"


@dataclass(frozen=True)
class ConsiliumRole:
    code: str
    title: str
    focus_domains: list[str] = field(default_factory=list)
    devil_role: bool = False


@dataclass(frozen=True)
class BranchReview:
    role_code: str
    branch_id: str
    position: ReviewPosition
    rationale: str
    evidence_ids: list[str] = field(default_factory=list)
    requested_evidence_ids: list[str] = field(default_factory=list)
    confidence: float = 0.5
    provenance: list[ProvenanceReference] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
        if not self.provenance:
            raise ValueError("branch review requires provenance")


@dataclass(frozen=True)
class MinorityOpinion:
    role_code: str
    branch_id: str
    position: ReviewPosition
    rationale: str


@dataclass(frozen=True)
class ConsiliumConsensus:
    retained_branch_ids: list[str]
    leading_branch_ids: list[str]
    unresolved_branch_ids: list[str]
    unsafe_to_close_branch_ids: list[str]
    minority_opinions: list[MinorityOpinion]
    missing_evidence_ids: list[str]
    prohibited_conclusions: list[str]
    summary: str


@dataclass(frozen=True)
class ConsiliumViolation:
    code: str
    explanation: str
    branch_ids: list[str] = field(default_factory=list)


@dataclass
class DynamicConsiliumResult:
    case_id: str
    branch_reviews: list[BranchReview]
    consensus: ConsiliumConsensus
    violations: list[ConsiliumViolation]
    warnings: list[str]
    limitations: list[str]


class DynamicConsiliumEngine:
    """Runs a structured review over a hypothesis graph without selecting a diagnosis."""

    def evaluate(
        self,
        case_id: str,
        branches: Iterable[HypothesisBranch],
        roles: Iterable[ConsiliumRole],
        reviews: Iterable[BranchReview],
        cluster_branch_ids: Iterable[Iterable[str]] = (),
    ) -> DynamicConsiliumResult:
        branch_list = list(branches)
        role_list = list(roles)
        review_list = list(reviews)
        branch_by_id = {branch.id: branch for branch in branch_list}
        role_by_code = {role.code: role for role in role_list}
        warnings: list[str] = []
        violations: list[ConsiliumViolation] = []

        if len(branch_by_id) != len(branch_list):
            raise ValueError("branch ids must be unique")
        if len(role_by_code) != len(role_list):
            raise ValueError("role codes must be unique")

        valid_reviews: list[BranchReview] = []
        for review in review_list:
            if review.branch_id not in branch_by_id:
                warnings.append(f"review_references_unknown_branch:{review.branch_id}")
                continue
            if review.role_code not in role_by_code:
                warnings.append(f"review_references_unknown_role:{review.role_code}")
                continue
            valid_reviews.append(review)

        reviewed_branch_ids = {review.branch_id for review in valid_reviews}
        missing_review_ids = sorted(set(branch_by_id) - reviewed_branch_ids)
        if missing_review_ids:
            violations.append(ConsiliumViolation(
                "branch_without_review",
                "Every active hypothesis branch must remain visible to the consilium.",
                missing_review_ids,
            ))

        by_branch: dict[str, list[BranchReview]] = {branch_id: [] for branch_id in branch_by_id}
        for review in valid_reviews:
            by_branch[review.branch_id].append(review)

        retained: list[str] = []
        leading: list[str] = []
        unresolved: list[str] = []
        unsafe_to_close: list[str] = []
        minority: list[MinorityOpinion] = []
        missing_evidence: set[str] = set()

        for branch in branch_list:
            branch_reviews = by_branch[branch.id]
            positions = [review.position for review in branch_reviews]
            for review in branch_reviews:
                missing_evidence.update(review.requested_evidence_ids)
            if branch.safety_critical or ReviewPosition.SAFETY_HOLD in positions:
                unsafe_to_close.append(branch.id)
            support_count = positions.count(ReviewPosition.SUPPORTS)
            weaken_count = positions.count(ReviewPosition.WEAKENS)
            if branch_reviews:
                retained.append(branch.id)
            if support_count > weaken_count and support_count >= 2:
                leading.append(branch.id)
            else:
                unresolved.append(branch.id)
            if len(set(positions)) > 1:
                majority = max(set(positions), key=positions.count)
                for review in branch_reviews:
                    if review.position != majority:
                        minority.append(MinorityOpinion(
                            role_code=review.role_code,
                            branch_id=branch.id,
                            position=review.position,
                            rationale=review.rationale,
                        ))

        clustered_ids = {branch_id for group in cluster_branch_ids for branch_id in group}
        if clustered_ids and not clustered_ids.issubset(set(retained)):
            missing = sorted(clustered_ids - set(retained))
            violations.append(ConsiliumViolation(
                "cluster_replaced_member_branches",
                "Mechanistic clusters must not replace their member branches in consilium output.",
                missing,
            ))

        if len(branch_list) > 1 and len(retained) <= 1:
            violations.append(ConsiliumViolation(
                "consilium_flattened_graph",
                "Consilium collapsed a multibranch graph into a single visible branch.",
                sorted(branch_by_id),
            ))

        if not any(role.devil_role for role in role_list):
            warnings.append("devil_role_missing")

        prohibited = [
            "diagnosis_confirmed",
            "single_cause_confirmed",
            "cluster_is_diagnosis",
            "consensus_is_diagnosis",
            "minority_opinion_discarded",
        ]
        consensus = ConsiliumConsensus(
            retained_branch_ids=sorted(retained),
            leading_branch_ids=sorted(leading),
            unresolved_branch_ids=sorted(set(unresolved)),
            unsafe_to_close_branch_ids=sorted(set(unsafe_to_close)),
            minority_opinions=minority,
            missing_evidence_ids=sorted(missing_evidence),
            prohibited_conclusions=prohibited,
            summary="Consensus summarizes structured review of branches; it does not establish diagnosis or causality.",
        )
        return DynamicConsiliumResult(
            case_id=case_id,
            branch_reviews=valid_reviews,
            consensus=consensus,
            violations=violations,
            warnings=sorted(set(warnings)),
            limitations=[
                "Consensus strength is not diagnostic probability.",
                "Minority opinions remain visible and may identify safety-critical alternatives.",
                "Mechanistic clusters are context for review, not final explanations.",
            ],
        )
