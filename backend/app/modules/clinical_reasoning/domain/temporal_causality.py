from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from itertools import combinations

from .causality import ProvenanceReference


class TemporalPrecision(str, Enum):
    EXACT = "exact"
    DAY = "day"
    MONTH = "month"
    YEAR = "year"
    INTERVAL = "interval"
    UNKNOWN = "unknown"


class TemporalRelationKind(str, Enum):
    BEFORE = "before"
    AFTER = "after"
    OVERLAPS = "overlaps"
    DURING = "during"
    CONTAINS = "contains"
    SAME_TIME = "same_time"
    POSSIBLY_BEFORE = "possibly_before"
    POSSIBLY_AFTER = "possibly_after"
    INDETERMINATE = "indeterminate"


class ClinicalEventKind(str, Enum):
    SYMPTOM = "symptom"
    LABORATORY_RESULT = "laboratory_result"
    IMAGING_FINDING = "imaging_finding"
    DIAGNOSIS = "diagnosis"
    MEDICATION_EXPOSURE = "medication_exposure"
    PROCEDURE = "procedure"
    INJURY = "injury"
    FUNCTIONAL_CHANGE = "functional_change"
    MECHANISM = "mechanism"
    CLINICAL_CONSEQUENCE = "clinical_consequence"
    OTHER = "other"


@dataclass(frozen=True)
class TemporalInterval:
    earliest_start: datetime | None = None
    latest_start: datetime | None = None
    earliest_end: datetime | None = None
    latest_end: datetime | None = None
    precision: TemporalPrecision = TemporalPrecision.UNKNOWN
    timezone: str | None = None

    def __post_init__(self) -> None:
        if self.earliest_start and self.latest_start and self.earliest_start > self.latest_start:
            raise ValueError("earliest_start cannot be after latest_start")
        if self.earliest_end and self.latest_end and self.earliest_end > self.latest_end:
            raise ValueError("earliest_end cannot be after latest_end")
        start_floor = self.earliest_start or self.latest_start
        end_ceiling = self.latest_end or self.earliest_end
        if start_floor and end_ceiling and start_floor > end_ceiling:
            raise ValueError("event start cannot be after event end")

    @property
    def start_min(self) -> datetime | None:
        return self.earliest_start or self.latest_start

    @property
    def start_max(self) -> datetime | None:
        return self.latest_start or self.earliest_start

    @property
    def end_min(self) -> datetime | None:
        return self.earliest_end or self.latest_end or self.start_min

    @property
    def end_max(self) -> datetime | None:
        return self.latest_end or self.earliest_end or self.start_max

    @property
    def is_known(self) -> bool:
        return any((self.earliest_start, self.latest_start, self.earliest_end, self.latest_end))


@dataclass
class ClinicalTimelineEvent:
    id: str
    case_id: str
    kind: ClinicalEventKind
    label: str
    interval: TemporalInterval
    provenance: list[ProvenanceReference]
    branch_ids: list[str] = field(default_factory=list)
    context: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id.strip() or not self.case_id.strip() or not self.label.strip():
            raise ValueError("event id, case_id and label are required")
        if not self.provenance:
            raise ValueError("timeline event requires provenance")


@dataclass(frozen=True)
class CausalTemporalLink:
    id: str
    source_event_id: str
    target_event_id: str
    relation_type: str
    provenance: list[ProvenanceReference]
    minimum_lag: timedelta | None = None
    maximum_lag: timedelta | None = None
    confidence: float = 0.5

    def __post_init__(self) -> None:
        if self.source_event_id == self.target_event_id:
            raise ValueError("causal temporal link cannot point to itself")
        if not self.provenance:
            raise ValueError("causal temporal link requires provenance")
        if not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
        if self.minimum_lag and self.minimum_lag < timedelta(0):
            raise ValueError("minimum_lag cannot be negative")
        if self.maximum_lag and self.maximum_lag < timedelta(0):
            raise ValueError("maximum_lag cannot be negative")
        if self.minimum_lag and self.maximum_lag and self.minimum_lag > self.maximum_lag:
            raise ValueError("minimum_lag cannot exceed maximum_lag")


@dataclass(frozen=True)
class TemporalRelation:
    source_event_id: str
    target_event_id: str
    relation_kind: TemporalRelationKind
    certainty: float
    explanation: str


@dataclass(frozen=True)
class TemporalConflict:
    id: str
    link_id: str
    conflict_type: str
    explanation: str
    severity: str
    source_event_id: str
    target_event_id: str


@dataclass(frozen=True)
class MissingTemporalEvidence:
    id: str
    event_ids: list[str]
    question: str
    rationale: str
    priority: str


@dataclass(frozen=True)
class BranchTemporalAssessment:
    branch_id: str
    event_ids: list[str]
    coherence_status: str
    conflict_ids: list[str]
    missing_evidence_ids: list[str]
    explanation: str


@dataclass
class TemporalCausalityResult:
    case_id: str
    ordered_event_ids: list[str]
    relations: list[TemporalRelation]
    conflicts: list[TemporalConflict]
    missing_evidence: list[MissingTemporalEvidence]
    branch_assessments: list[BranchTemporalAssessment]
    limitations: list[str]
    warnings: list[str]


class TemporalCausalityEngine:
    """Conservative temporal reasoning for clinical causal graphs.

    Uncertain or partial dates remain intervals. The engine never invents exact
    dates and never converts temporal precedence alone into causality.
    """

    def evaluate(
        self,
        case_id: str,
        events: list[ClinicalTimelineEvent],
        causal_links: list[CausalTemporalLink],
    ) -> TemporalCausalityResult:
        event_map = {event.id: event for event in events}
        if len(event_map) != len(events):
            raise ValueError("event ids must be unique")
        if any(event.case_id != case_id for event in events):
            raise ValueError("all events must belong to case_id")

        relations = [self.compare(left, right) for left, right in combinations(events, 2)]
        conflicts: list[TemporalConflict] = []
        missing: list[MissingTemporalEvidence] = []
        warnings: list[str] = []

        for link in causal_links:
            source = event_map.get(link.source_event_id)
            target = event_map.get(link.target_event_id)
            if source is None or target is None:
                warnings.append("causal_link_references_unknown_event")
                continue
            conflict = self._evaluate_link(link, source, target)
            if conflict:
                conflicts.append(conflict)
            elif not source.interval.is_known or not target.interval.is_known:
                missing.append(self._missing_for_link(link, source, target, "Event timing is unknown."))
            elif not self._order_definitely_supported(source.interval, target.interval, link.minimum_lag):
                missing.append(
                    self._missing_for_link(
                        link,
                        source,
                        target,
                        "Available intervals overlap or are too imprecise to establish the required order.",
                    )
                )

        for event in events:
            if not event.interval.is_known:
                missing.append(
                    MissingTemporalEvidence(
                        id=f"{case_id}:missing:event:{event.id}",
                        event_ids=[event.id],
                        question=f"When did '{event.label}' begin and, if applicable, end?",
                        rationale="Temporal placement is required to test causal direction without inventing a date.",
                        priority="standard",
                    )
                )

        branch_assessments = self._assess_branches(events, conflicts, missing)
        ordered = [
            event.id
            for event in sorted(
                events,
                key=lambda item: (
                    item.interval.start_min is None,
                    item.interval.start_min or datetime.max,
                    item.id,
                ),
            )
        ]
        limitations = [
            "Temporal precedence can support or weaken a causal hypothesis but does not establish causality."
        ]
        if any(not event.interval.is_known for event in events):
            limitations.append("One or more events have unknown timing and remain unplaced or partially placed.")

        return TemporalCausalityResult(
            case_id=case_id,
            ordered_event_ids=ordered,
            relations=relations,
            conflicts=conflicts,
            missing_evidence=self._deduplicate_missing(missing),
            branch_assessments=branch_assessments,
            limitations=limitations,
            warnings=sorted(set(warnings)),
        )

    def compare(self, left: ClinicalTimelineEvent, right: ClinicalTimelineEvent) -> TemporalRelation:
        a, b = left.interval, right.interval
        if not a.is_known or not b.is_known:
            return TemporalRelation(left.id, right.id, TemporalRelationKind.INDETERMINATE, 0.0, "At least one event has unknown timing.")
        if a.end_max and b.start_min and a.end_max < b.start_min:
            return TemporalRelation(left.id, right.id, TemporalRelationKind.BEFORE, 1.0, "The latest possible end of the first event precedes the earliest possible start of the second.")
        if b.end_max and a.start_min and b.end_max < a.start_min:
            return TemporalRelation(left.id, right.id, TemporalRelationKind.AFTER, 1.0, "The second event definitely precedes the first.")
        if a.start_min == a.start_max == b.start_min == b.start_max and a.end_min == a.end_max == b.end_min == b.end_max:
            return TemporalRelation(left.id, right.id, TemporalRelationKind.SAME_TIME, 1.0, "Both events have the same exact interval.")
        if self._definitely_contains(a, b):
            return TemporalRelation(left.id, right.id, TemporalRelationKind.CONTAINS, 0.9, "The second event is bounded by the first event interval.")
        if self._definitely_contains(b, a):
            return TemporalRelation(left.id, right.id, TemporalRelationKind.DURING, 0.9, "The first event is bounded by the second event interval.")
        if self._may_overlap(a, b):
            return TemporalRelation(left.id, right.id, TemporalRelationKind.OVERLAPS, 0.5, "The possible intervals overlap; exact order is unresolved.")
        if a.start_min and b.start_max and a.start_min < b.start_max:
            return TemporalRelation(left.id, right.id, TemporalRelationKind.POSSIBLY_BEFORE, 0.25, "The first event may precede the second, but the intervals are imprecise.")
        return TemporalRelation(left.id, right.id, TemporalRelationKind.INDETERMINATE, 0.0, "Available intervals do not establish order.")

    def _evaluate_link(self, link: CausalTemporalLink, source: ClinicalTimelineEvent, target: ClinicalTimelineEvent) -> TemporalConflict | None:
        source_start = source.interval.start_min
        target_end = target.interval.end_max
        if source_start and target_end and target_end < source_start:
            return TemporalConflict(
                id=f"{link.id}:cause_after_effect",
                link_id=link.id,
                conflict_type="cause_after_effect",
                explanation="The proposed causal source begins after the target event has already ended.",
                severity="high",
                source_event_id=source.id,
                target_event_id=target.id,
            )
        if link.minimum_lag and source.interval.end_max and target.interval.start_max:
            if target.interval.start_max < source.interval.end_max + link.minimum_lag:
                return TemporalConflict(
                    id=f"{link.id}:minimum_lag_violation",
                    link_id=link.id,
                    conflict_type="minimum_lag_violation",
                    explanation="The maximum possible target start is earlier than the required minimum lag.",
                    severity="moderate",
                    source_event_id=source.id,
                    target_event_id=target.id,
                )
        if link.maximum_lag and source.interval.start_min and target.interval.start_min:
            if target.interval.start_min > source.interval.start_min + link.maximum_lag:
                return TemporalConflict(
                    id=f"{link.id}:maximum_lag_violation",
                    link_id=link.id,
                    conflict_type="maximum_lag_violation",
                    explanation="The earliest target start is later than the allowed maximum lag.",
                    severity="moderate",
                    source_event_id=source.id,
                    target_event_id=target.id,
                )
        return None

    @staticmethod
    def _order_definitely_supported(source: TemporalInterval, target: TemporalInterval, minimum_lag: timedelta | None) -> bool:
        if source.end_max is None or target.start_min is None:
            return False
        lag = minimum_lag or timedelta(0)
        return source.end_max + lag <= target.start_min

    @staticmethod
    def _definitely_contains(outer: TemporalInterval, inner: TemporalInterval) -> bool:
        return bool(
            outer.start_max and outer.end_min and inner.start_min and inner.end_max
            and outer.start_max <= inner.start_min
            and inner.end_max <= outer.end_min
        )

    @staticmethod
    def _may_overlap(left: TemporalInterval, right: TemporalInterval) -> bool:
        return bool(
            left.start_min and left.end_max and right.start_min and right.end_max
            and left.start_min <= right.end_max
            and right.start_min <= left.end_max
        )

    @staticmethod
    def _missing_for_link(link: CausalTemporalLink, source: ClinicalTimelineEvent, target: ClinicalTimelineEvent, rationale: str) -> MissingTemporalEvidence:
        return MissingTemporalEvidence(
            id=f"{link.id}:missing_order",
            event_ids=[source.id, target.id],
            question=f"What is the reliable temporal order between '{source.label}' and '{target.label}'?",
            rationale=rationale,
            priority="high" if link.confidence >= 0.7 else "standard",
        )

    @staticmethod
    def _deduplicate_missing(items: list[MissingTemporalEvidence]) -> list[MissingTemporalEvidence]:
        unique: dict[str, MissingTemporalEvidence] = {}
        for item in items:
            unique[item.id] = item
        return list(unique.values())

    @staticmethod
    def _assess_branches(
        events: list[ClinicalTimelineEvent],
        conflicts: list[TemporalConflict],
        missing: list[MissingTemporalEvidence],
    ) -> list[BranchTemporalAssessment]:
        branch_ids = sorted({branch_id for event in events for branch_id in event.branch_ids})
        results: list[BranchTemporalAssessment] = []
        for branch_id in branch_ids:
            event_ids = [event.id for event in events if branch_id in event.branch_ids]
            conflict_ids = [c.id for c in conflicts if c.source_event_id in event_ids or c.target_event_id in event_ids]
            missing_ids = [m.id for m in missing if any(event_id in event_ids for event_id in m.event_ids)]
            if conflict_ids:
                status = "conflicted"
            elif missing_ids:
                status = "indeterminate"
            else:
                status = "temporally_coherent"
            results.append(
                BranchTemporalAssessment(
                    branch_id=branch_id,
                    event_ids=event_ids,
                    coherence_status=status,
                    conflict_ids=conflict_ids,
                    missing_evidence_ids=missing_ids,
                    explanation="Temporal coherence is assessed independently from diagnostic probability.",
                )
            )
        return results
