from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from itertools import combinations
from typing import Iterable

from .causality import ContextConstraint, ProvenanceReference
from .hypothesis_expansion import HypothesisBranch


class ClusterType(str, Enum):
    SHARED_UPSTREAM_MECHANISM = "shared_upstream_mechanism"
    SHARED_DOWNSTREAM_CONSEQUENCE = "shared_downstream_consequence"
    COMMON_RISK_FACTOR = "common_risk_factor"
    CROSS_SYSTEM_CLUSTER = "cross_system_cluster"


class ClusterConflictType(str, Enum):
    SHARED_CONSEQUENCE_TREATED_AS_SHARED_CAUSE = "shared_consequence_treated_as_shared_cause"
    SHARED_RISK_FACTOR_TREATED_AS_SINGLE_MECHANISM = "shared_risk_factor_treated_as_single_mechanism"
    CLUSTER_REPLACED_MEMBER_BRANCHES = "cluster_replaced_member_branches"
    INSUFFICIENT_PROVENANCE = "insufficient_provenance"
    CONTEXT_CONSTRAINT_MISMATCH = "context_constraint_mismatch"


@dataclass(frozen=True)
class BranchMechanisticProfile:
    branch_id: str
    body_systems: list[str]
    upstream_mechanism_ids: list[str] = field(default_factory=list)
    downstream_consequence_ids: list[str] = field(default_factory=list)
    risk_factor_ids: list[str] = field(default_factory=list)
    provenance: list[ProvenanceReference] = field(default_factory=list)
    context_constraints: list[ContextConstraint] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.branch_id.strip():
            raise ValueError("branch_id is required")
        if not self.provenance:
            raise ValueError("mechanistic profile requires provenance")


@dataclass(frozen=True)
class CrossSystemCluster:
    id: str
    case_id: str
    name: str
    cluster_type: ClusterType
    branch_ids: list[str]
    body_systems: list[str]
    shared_item_ids: list[str]
    evidence_strength: str
    confidence: float
    provenance: list[ProvenanceReference]
    context_constraints: list[ContextConstraint]
    member_branches_preserved: bool = True


@dataclass(frozen=True)
class ClusterConflict:
    code: ClusterConflictType
    cluster_id: str | None
    branch_ids: list[str]
    explanation: str


@dataclass
class MechanisticClusteringResult:
    case_id: str
    branches: list[HypothesisBranch]
    clusters: list[CrossSystemCluster]
    conflicts: list[ClusterConflict]
    independent_branch_ids: list[str]
    limitations: list[str]
    warnings: list[str]


class MechanisticClusteringEngine:
    """Builds cross-system clusters without turning a cluster into a diagnosis."""

    def cluster(
        self,
        case_id: str,
        branches: Iterable[HypothesisBranch],
        profiles: Iterable[BranchMechanisticProfile],
    ) -> MechanisticClusteringResult:
        branch_list = list(branches)
        profile_list = list(profiles)
        branch_by_id = {branch.id: branch for branch in branch_list}
        warnings: list[str] = []
        conflicts: list[ClusterConflict] = []

        valid_profiles = []
        for profile in profile_list:
            if profile.branch_id not in branch_by_id:
                warnings.append(f"profile_references_unknown_branch:{profile.branch_id}")
                continue
            valid_profiles.append(profile)

        clusters: list[CrossSystemCluster] = []
        clusters.extend(self._build_clusters(case_id, valid_profiles, "upstream_mechanism_ids", ClusterType.SHARED_UPSTREAM_MECHANISM))
        clusters.extend(self._build_clusters(case_id, valid_profiles, "downstream_consequence_ids", ClusterType.SHARED_DOWNSTREAM_CONSEQUENCE))
        clusters.extend(self._build_clusters(case_id, valid_profiles, "risk_factor_ids", ClusterType.COMMON_RISK_FACTOR))

        clustered_branch_ids = {bid for cluster in clusters for bid in cluster.branch_ids}
        independent = sorted(set(branch_by_id) - clustered_branch_ids)

        for cluster in clusters:
            if cluster.cluster_type == ClusterType.SHARED_DOWNSTREAM_CONSEQUENCE:
                conflicts.append(ClusterConflict(
                    ClusterConflictType.SHARED_CONSEQUENCE_TREATED_AS_SHARED_CAUSE,
                    cluster.id,
                    cluster.branch_ids,
                    "A shared downstream consequence does not prove a shared upstream cause.",
                ))
            if cluster.cluster_type == ClusterType.COMMON_RISK_FACTOR:
                conflicts.append(ClusterConflict(
                    ClusterConflictType.SHARED_RISK_FACTOR_TREATED_AS_SINGLE_MECHANISM,
                    cluster.id,
                    cluster.branch_ids,
                    "A common risk factor may contribute to several independent mechanisms.",
                ))
            if not cluster.member_branches_preserved:
                conflicts.append(ClusterConflict(
                    ClusterConflictType.CLUSTER_REPLACED_MEMBER_BRANCHES,
                    cluster.id,
                    cluster.branch_ids,
                    "Cluster output must preserve all member branches.",
                ))

        limitations = [
            "Clusters are mechanistic groupings, not diagnoses.",
            "Shared items may be correlational unless supported by directional evidence.",
        ]
        if not clusters:
            limitations.append("No cross-system cluster met the minimum two-branch overlap rule.")

        return MechanisticClusteringResult(
            case_id=case_id,
            branches=branch_list,
            clusters=clusters,
            conflicts=conflicts,
            independent_branch_ids=independent,
            limitations=limitations,
            warnings=warnings,
        )

    def _build_clusters(
        self,
        case_id: str,
        profiles: list[BranchMechanisticProfile],
        attribute: str,
        cluster_type: ClusterType,
    ) -> list[CrossSystemCluster]:
        item_to_profiles: dict[str, list[BranchMechanisticProfile]] = {}
        for profile in profiles:
            for item in set(getattr(profile, attribute)):
                item_to_profiles.setdefault(item, []).append(profile)

        clusters: list[CrossSystemCluster] = []
        for item, members in sorted(item_to_profiles.items()):
            if len(members) < 2:
                continue
            branch_ids = sorted({member.branch_id for member in members})
            systems = sorted({system for member in members for system in member.body_systems})
            provenance = self._merge_provenance(members)
            constraints = self._common_constraints(members)
            cross_system = len(systems) > 1
            effective_type = ClusterType.CROSS_SYSTEM_CLUSTER if cross_system and cluster_type == ClusterType.SHARED_UPSTREAM_MECHANISM else cluster_type
            confidence = min(0.9, 0.45 + 0.1 * len(branch_ids) + (0.1 if provenance else 0.0))
            clusters.append(CrossSystemCluster(
                id=f"{case_id}:cluster:{cluster_type.value}:{item}",
                case_id=case_id,
                name=f"{cluster_type.value.replace('_', ' ').title()}: {item}",
                cluster_type=effective_type,
                branch_ids=branch_ids,
                body_systems=systems,
                shared_item_ids=[item],
                evidence_strength="plausible" if len(provenance) == 1 else "supported",
                confidence=round(confidence, 3),
                provenance=provenance,
                context_constraints=constraints,
                member_branches_preserved=True,
            ))
        return clusters

    @staticmethod
    def _merge_provenance(members: list[BranchMechanisticProfile]) -> list[ProvenanceReference]:
        unique = {}
        for member in members:
            for item in member.provenance:
                unique[(item.source_id, item.source_version, item.locator)] = item
        return list(unique.values())

    @staticmethod
    def _common_constraints(members: list[BranchMechanisticProfile]) -> list[ContextConstraint]:
        if not members:
            return []
        common = {(c.key, c.operator, repr(c.value)): c for c in members[0].context_constraints}
        for member in members[1:]:
            keys = {(c.key, c.operator, repr(c.value)) for c in member.context_constraints}
            common = {key: value for key, value in common.items() if key in keys}
        return list(common.values())
