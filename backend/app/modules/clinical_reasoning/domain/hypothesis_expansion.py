from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable

from .causality import CausalPath, ContextConstraint, ProvenanceReference


class BranchStatus(str, Enum):
    GENERATED = "generated"
    ACTIVE = "active"
    SUPPORTED = "supported"
    WEAKLY_SUPPORTED = "weakly_supported"
    CONTRADICTED = "contradicted"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    DEPRIORITIZED = "deprioritized"
    CLOSED = "closed"
    UNSAFE_TO_CLOSE = "unsafe_to_close"


class BranchRelationshipType(str, Enum):
    COMPETES_WITH = "competes_with"
    ALTERNATIVE_TO = "alternative_to"
    COMPATIBLE_WITH = "compatible_with"
    MAY_COEXIST_WITH = "may_coexist_with"
    MAY_CAUSE = "may_cause"
    MAY_CONTRIBUTE_TO = "may_contribute_to"
    MAY_AMPLIFY = "may_amplify"
    MAY_RESULT_FROM = "may_result_from"
    SHARES_MECHANISM_WITH = "shares_mechanism_with"
    SHARES_RISK_FACTOR_WITH = "shares_risk_factor_with"
    SHARES_CONSEQUENCE_WITH = "shares_consequence_with"
    DEPENDS_ON = "depends_on"
    REQUIRES_EXCLUSION_OF = "requires_exclusion_of"
    TEMPORALLY_PRECEDES = "temporally_precedes"
    TEMPORALLY_FOLLOWS = "temporally_follows"


@dataclass
class HypothesisBranch:
    id: str
    case_id: str
    title: str
    description: str
    root_trigger_ids: list[str]
    causal_domain: str
    branch_type: str
    node_ids: list[str]
    edge_ids: list[str]
    supporting_fact_ids: list[str] = field(default_factory=list)
    contradicting_fact_ids: list[str] = field(default_factory=list)
    neutral_fact_ids: list[str] = field(default_factory=list)
    missing_evidence_ids: list[str] = field(default_factory=list)
    evidence_strength: str = "plausible"
    confidence: float = 0.5
    status: BranchStatus = BranchStatus.GENERATED
    provenance: list[ProvenanceReference] = field(default_factory=list)
    context_constraints: list[ContextConstraint] = field(default_factory=list)
    safety_critical: bool = False

    def __post_init__(self) -> None:
        if not self.provenance:
            raise ValueError("branch requires provenance")
        if not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")

    @property
    def independence_key(self) -> tuple[str, tuple[str, ...], tuple[str, ...]]:
        return (self.causal_domain.lower(), tuple(self.node_ids), tuple(self.edge_ids))


@dataclass
class BranchRelationship:
    id: str
    source_branch_id: str
    target_branch_id: str
    relationship_type: BranchRelationshipType
    explanation: str
    evidence_strength: str
    confidence: float
    provenance: list[ProvenanceReference]
    context_constraints: list[ContextConstraint] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.source_branch_id == self.target_branch_id:
            raise ValueError("branch relationship cannot point to itself")
        if not self.provenance:
            raise ValueError("branch relationship requires provenance")


@dataclass
class MechanisticCluster:
    id: str
    name: str
    branch_ids: list[str]
    shared_mechanism_ids: list[str]
    shared_fact_ids: list[str]
    shared_consequence_ids: list[str]
    cluster_type: str
    confidence: float
    evidence_strength: str
    provenance: list[ProvenanceReference]


@dataclass
class DiscriminatingEvidence:
    id: str
    proposed_data_item: str
    affected_branch_ids: list[str]
    rationale: str
    information_gain: float
    clinical_utility: float
    safety_priority: float
    provenance: list[ProvenanceReference]


@dataclass
class ExpansionSafetyFlag:
    code: str
    branch_id: str | None
    explanation: str


@dataclass
class HypothesisExpansionResult:
    case_id: str
    branches: list[HypothesisBranch]
    relationships: list[BranchRelationship]
    clusters: list[MechanisticCluster]
    discriminators: list[DiscriminatingEvidence]
    safety_flags: list[ExpansionSafetyFlag]
    limitations: list[str]
    violations: list[str]


class DominanceGuard:
    def evaluate(self, branches: list[HypothesisBranch], clusters: list[MechanisticCluster] | None = None) -> list[str]:
        violations: list[str] = []
        if not branches:
            return ["single_branch_without_alternatives: no branches generated"]
        if len(branches) == 1:
            violations.append("single_branch_without_alternatives")
        seen: dict[tuple, str] = {}
        for branch in branches:
            if branch.independence_key in seen:
                violations.append(f"duplicate_branch:{branch.id}:{seen[branch.independence_key]}")
            seen[branch.independence_key] = branch.id
            if branch.status == BranchStatus.CLOSED and not branch.contradicting_fact_ids:
                violations.append(f"branch_closed_without_evidence:{branch.id}")
            if not branch.provenance:
                violations.append(f"missing_provenance:{branch.id}")
        branch_ids = {b.id for b in branches}
        for cluster in clusters or []:
            if not set(cluster.branch_ids).issubset(branch_ids):
                violations.append(f"cluster_replaced_independent_branches:{cluster.id}")
        return violations


class BranchExpansionEngine:
    """Domain-neutral expansion over causal paths. It never emits a diagnosis."""

    def expand(self, case_id: str, causal_paths: Iterable[CausalPath]) -> HypothesisExpansionResult:
        paths = list(causal_paths)
        branches: list[HypothesisBranch] = []
        for index, path in enumerate(paths, 1):
            branches.append(
                HypothesisBranch(
                    id=f"{case_id}:branch:{index}",
                    case_id=case_id,
                    title=f"{path.causal_domain.replace('_', ' ').title()} mechanism branch",
                    description="Candidate mechanistic branch; not a diagnosis.",
                    root_trigger_ids=[path.node_ids[0]],
                    causal_domain=path.causal_domain,
                    branch_type="primary_mechanistic" if index == 1 else "alternative_mechanistic",
                    node_ids=list(path.node_ids),
                    edge_ids=list(path.edge_ids),
                    missing_evidence_ids=[path.node_ids[-1]] if "missing" in path.node_ids[-1].lower() else [],
                    provenance=list(path.provenance),
                    context_constraints=list(path.context_constraints),
                )
            )

        relationships: list[BranchRelationship] = []
        for i, left in enumerate(branches):
            for right in branches[i + 1 :]:
                shared = set(left.node_ids) & set(right.node_ids)
                relation_type = (
                    BranchRelationshipType.SHARES_MECHANISM_WITH
                    if len(shared) > 1
                    else BranchRelationshipType.MAY_COEXIST_WITH
                )
                provenance = list({(p.source_id, p.source_version, p.locator): p for p in left.provenance + right.provenance}.values())
                relationships.append(
                    BranchRelationship(
                        id=f"{left.id}->{right.id}",
                        source_branch_id=left.id,
                        target_branch_id=right.id,
                        relationship_type=relation_type,
                        explanation="Branches share graph context but remain independently testable.",
                        evidence_strength="plausible",
                        confidence=0.5,
                        provenance=provenance,
                    )
                )

        clusters: list[MechanisticCluster] = []
        cardiometabolic = [b for b in branches if b.causal_domain in {"glycemic_regulation", "lipid_metabolism", "hepatic_integrity"}]
        if len(cardiometabolic) >= 2:
            prov = list({(p.source_id, p.source_version, p.locator): p for b in cardiometabolic for p in b.provenance}.values())
            clusters.append(
                MechanisticCluster(
                    id=f"{case_id}:cluster:cardiometabolic",
                    name="Possible cardiometabolic mechanistic cluster",
                    branch_ids=[b.id for b in cardiometabolic],
                    shared_mechanism_ids=[],
                    shared_fact_ids=sorted(set.intersection(*(set(b.root_trigger_ids) for b in cardiometabolic))) if cardiometabolic else [],
                    shared_consequence_ids=[],
                    cluster_type="possible_multisystem_process",
                    confidence=0.45,
                    evidence_strength="plausible",
                    provenance=prov,
                )
            )

        discriminators: list[DiscriminatingEvidence] = []
        if len(branches) > 1:
            prov = list({(p.source_id, p.source_version, p.locator): p for b in branches for p in b.provenance}.values())
            discriminators.append(
                DiscriminatingEvidence(
                    id=f"{case_id}:discriminator:timeline",
                    proposed_data_item="Clinical timeline and repeat measurements in the relevant context",
                    affected_branch_ids=[b.id for b in branches],
                    rationale="Temporal order and persistence can separate primary, secondary, transient, and treatment-modified mechanisms.",
                    information_gain=0.75,
                    clinical_utility=0.7,
                    safety_priority=0.4,
                    provenance=prov,
                )
            )

        safety_flags = [
            ExpansionSafetyFlag("unsafe_to_close", b.id, "Safety-critical branch lacks sufficient contradicting evidence.")
            for b in branches if b.safety_critical and not b.contradicting_fact_ids
        ]
        violations = DominanceGuard().evaluate(branches, clusters)
        return HypothesisExpansionResult(
            case_id=case_id,
            branches=branches,
            relationships=relationships,
            clusters=clusters,
            discriminators=discriminators,
            safety_flags=safety_flags,
            limitations=["Mechanistic expansion is hypothesis-generating and does not establish diagnosis or causality."],
            violations=violations,
        )
