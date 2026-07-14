from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Iterable

from .causality import ContextConstraint, ProvenanceReference
from .hypothesis_expansion import HypothesisBranch


class LoadExposureKind(str, Enum):
    DAILY_ACTIVITY = "daily_activity"
    OCCUPATIONAL = "occupational"
    TRAINING = "training"
    ACUTE_EVENT = "acute_event"
    IMMOBILITY = "immobility"
    UNKNOWN = "unknown"


class AdaptationState(str, Enum):
    POSITIVE = "positive"
    ADEQUATE = "adequate"
    INSUFFICIENT = "insufficient"
    MALADAPTIVE = "maladaptive"
    UNKNOWN = "unknown"


class OverloadPattern(str, Enum):
    ACUTE_SPIKE = "acute_spike"
    CHRONIC_EXCESS = "chronic_excess"
    REPETITIVE_EXPOSURE = "repetitive_exposure"
    CAPACITY_DEMAND_MISMATCH = "capacity_demand_mismatch"
    RECOVERY_DEFICIT = "recovery_deficit"
    DECONDITIONING = "deconditioning"
    NONE_IDENTIFIED = "none_identified"
    INDETERMINATE = "indeterminate"


class LoadEvidenceEffectType(str, Enum):
    SUPPORTS = "supports"
    WEAKENS = "weakens"
    NON_DISCRIMINATING = "non_discriminating"
    CHANGES_CONTEXT = "changes_context"
    CHANGES_URGENCY = "changes_urgency"


@dataclass(frozen=True)
class LoadExposure:
    id: str
    kind: LoadExposureKind
    code: str
    magnitude: float | None = None
    duration_minutes: float | None = None
    frequency_per_week: float | None = None
    occurred_at: datetime | None = None
    body_region: str | None = None
    provenance: list[ProvenanceReference] = field(default_factory=list)
    context_constraints: list[ContextConstraint] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.id.strip() or not self.code.strip():
            raise ValueError("load exposure requires id and code")
        if not self.provenance:
            raise ValueError("load exposure requires provenance")
        for value, label in ((self.magnitude, "magnitude"), (self.duration_minutes, "duration"), (self.frequency_per_week, "frequency")):
            if value is not None and value < 0:
                raise ValueError(f"{label} cannot be negative")


@dataclass(frozen=True)
class RecoveryCapacity:
    id: str
    sleep_quality: float | None = None
    recovery_hours: float | None = None
    baseline_capacity: float | None = None
    current_capacity: float | None = None
    limiting_factors: tuple[str, ...] = ()
    provenance: list[ProvenanceReference] = field(default_factory=list)
    context_constraints: list[ContextConstraint] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.id.strip() or not self.provenance:
            raise ValueError("recovery capacity requires id and provenance")
        for value in (self.sleep_quality, self.baseline_capacity, self.current_capacity):
            if value is not None and not 0 <= value <= 1:
                raise ValueError("capacity fractions must be between 0 and 1")
        if self.recovery_hours is not None and self.recovery_hours < 0:
            raise ValueError("recovery hours cannot be negative")


@dataclass(frozen=True)
class LoadResponseObservation:
    id: str
    exposure_id: str
    symptom_change: float | None = None
    onset_delay_hours: float | None = None
    recovery_time_hours: float | None = None
    functional_change: str | None = None
    repeated_pattern: bool | None = None
    provenance: list[ProvenanceReference] = field(default_factory=list)
    context_constraints: list[ContextConstraint] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.id.strip() or not self.exposure_id.strip() or not self.provenance:
            raise ValueError("load response requires ids and provenance")
        if self.onset_delay_hours is not None and self.onset_delay_hours < 0:
            raise ValueError("onset delay cannot be negative")
        if self.recovery_time_hours is not None and self.recovery_time_hours < 0:
            raise ValueError("recovery time cannot be negative")


@dataclass(frozen=True)
class CapacityDemandMismatch:
    exposure_id: str
    demand: float
    capacity: float
    mismatch: float
    rationale: str


@dataclass(frozen=True)
class BranchLoadEffect:
    branch_id: str
    evidence_id: str
    effect_type: LoadEvidenceEffectType
    strength: str
    rationale: str
    provenance: list[ProvenanceReference]
    context_constraints: list[ContextConstraint] = field(default_factory=list)


@dataclass(frozen=True)
class MissingLoadEvidence:
    id: str
    branch_id: str
    required_item: str
    rationale: str
    provenance: list[ProvenanceReference]


@dataclass
class BranchLoadAssessment:
    branch_id: str
    supporting_evidence_ids: list[str]
    weakening_evidence_ids: list[str]
    contextual_evidence_ids: list[str]
    urgency_evidence_ids: list[str]
    overload_patterns: list[OverloadPattern]
    adaptation_state: AdaptationState
    missing_evidence_ids: list[str]


@dataclass
class BiomechanicalLoadResult:
    case_id: str
    mismatches: list[CapacityDemandMismatch]
    effects: list[BranchLoadEffect]
    branch_assessments: list[BranchLoadAssessment]
    missing_evidence: list[MissingLoadEvidence]
    unassigned_exposure_ids: list[str]
    limitations: list[str]
    prohibited_conclusions: list[str]


LOAD_RELEVANT_DOMAINS = {
    "muscle_tendon", "biomechanical_load", "degenerative", "local_joint",
    "traumatic", "lumbar_radicular", "iatrogenic_or_postoperative",
}


class BiomechanicalLoadEngine:
    """Evaluates load/capacity/recovery context without inferring injury or diagnosis."""

    def evaluate(
        self,
        case_id: str,
        branches: Iterable[HypothesisBranch],
        exposures: Iterable[LoadExposure],
        recovery: RecoveryCapacity | None,
        responses: Iterable[LoadResponseObservation],
    ) -> BiomechanicalLoadResult:
        branch_list = list(branches)
        exposure_list = list(exposures)
        response_list = list(responses)
        exposure_by_id = {item.id: item for item in exposure_list}
        response_by_exposure: dict[str, list[LoadResponseObservation]] = {}
        for response in response_list:
            response_by_exposure.setdefault(response.exposure_id, []).append(response)

        capacity = self._capacity(recovery)
        mismatches: list[CapacityDemandMismatch] = []
        for exposure in exposure_list:
            demand = self._demand(exposure)
            mismatch = max(0.0, demand - capacity)
            mismatches.append(CapacityDemandMismatch(
                exposure.id, demand, capacity, mismatch,
                "Demand exceeds estimated current capacity." if mismatch > 0 else "No quantified capacity-demand excess identified.",
            ))

        effects: list[BranchLoadEffect] = []
        assigned_exposures: set[str] = set()
        branch_assessments: list[BranchLoadAssessment] = []
        missing: list[MissingLoadEvidence] = []
        provenance = self._fallback_provenance(exposure_list, recovery, response_list)

        for branch in branch_list:
            domain = branch.causal_domain
            supporting: list[str] = []
            weakening: list[str] = []
            contextual: list[str] = []
            urgent: list[str] = []
            patterns: set[OverloadPattern] = set()

            if domain in LOAD_RELEVANT_DOMAINS:
                for mismatch in mismatches:
                    exposure = exposure_by_id[mismatch.exposure_id]
                    responses_for_exposure = response_by_exposure.get(exposure.id, [])
                    repeated = any(item.repeated_pattern is True for item in responses_for_exposure)
                    worsened = any((item.symptom_change or 0) > 0 for item in responses_for_exposure)
                    recovered = any(item.recovery_time_hours is not None for item in responses_for_exposure)

                    if mismatch.mismatch > 0:
                        patterns.add(OverloadPattern.CAPACITY_DEMAND_MISMATCH)
                        effect_type = LoadEvidenceEffectType.SUPPORTS if domain in {"biomechanical_load", "muscle_tendon"} else LoadEvidenceEffectType.CHANGES_CONTEXT
                        effects.append(self._effect(branch.id, exposure, effect_type, "moderate", "Capacity-demand mismatch may support a load-related mechanism but does not prove tissue injury."))
                        (supporting if effect_type == LoadEvidenceEffectType.SUPPORTS else contextual).append(exposure.id)
                        assigned_exposures.add(exposure.id)
                    else:
                        effects.append(self._effect(branch.id, exposure, LoadEvidenceEffectType.NON_DISCRIMINATING, "contextual", "Recorded exposure does not quantify an excess and does not exclude load sensitivity."))
                        contextual.append(exposure.id)

                    if exposure.kind == LoadExposureKind.ACUTE_EVENT and mismatch.mismatch > 0:
                        patterns.add(OverloadPattern.ACUTE_SPIKE)
                    elif exposure.kind in {LoadExposureKind.OCCUPATIONAL, LoadExposureKind.TRAINING, LoadExposureKind.DAILY_ACTIVITY} and (exposure.frequency_per_week or 0) >= 5:
                        patterns.add(OverloadPattern.REPETITIVE_EXPOSURE)
                    if repeated and worsened:
                        patterns.add(OverloadPattern.CHRONIC_EXCESS if exposure.kind != LoadExposureKind.ACUTE_EVENT else OverloadPattern.ACUTE_SPIKE)
                        effects.append(self._effect(branch.id, exposure, LoadEvidenceEffectType.SUPPORTS, "moderate", "Repeated symptom response increases coherence of a load-response pattern; it does not identify damaged tissue."))
                        supporting.append(exposure.id)
                    if recovered and not worsened:
                        effects.append(self._effect(branch.id, exposure, LoadEvidenceEffectType.WEAKENS, "weak", "Stable or improving function after exposure weakens a persistent overload interpretation without excluding it."))
                        weakening.append(exposure.id)

                if recovery is None:
                    missing.append(MissingLoadEvidence(f"missing:{branch.id}:recovery", branch.id, "recovery_capacity", "Recovery capacity is required to interpret load tolerance.", provenance))
                else:
                    if recovery.current_capacity is not None and recovery.baseline_capacity is not None and recovery.current_capacity < recovery.baseline_capacity:
                        patterns.add(OverloadPattern.DECONDITIONING)
                    if recovery.recovery_hours is not None and recovery.recovery_hours < 12:
                        patterns.add(OverloadPattern.RECOVERY_DEFICIT)
                    if recovery.limiting_factors:
                        patterns.add(OverloadPattern.RECOVERY_DEFICIT)

                adaptation = self._adaptation(patterns, response_list)
                required = []
                if not exposure_list:
                    required.append("load_exposure_history")
                if not response_list:
                    required.append("load_response_observation")
                for item in required:
                    missing.append(MissingLoadEvidence(f"missing:{branch.id}:{item}", branch.id, item, "Missing data must not be interpreted as a negative load-response finding.", provenance))
            else:
                adaptation = AdaptationState.UNKNOWN

            branch_missing = [item.id for item in missing if item.branch_id == branch.id]
            branch_assessments.append(BranchLoadAssessment(
                branch.id, sorted(set(supporting)), sorted(set(weakening)), sorted(set(contextual)), sorted(set(urgent)),
                sorted(patterns, key=lambda item: item.value) or [OverloadPattern.INDETERMINATE], adaptation, branch_missing,
            ))

        unassigned = sorted({item.id for item in exposure_list} - assigned_exposures)
        return BiomechanicalLoadResult(
            case_id, mismatches, effects, branch_assessments, missing, unassigned,
            [
                "Load estimates are contextual and depend on measurement quality.",
                "Observed symptom response may reflect sensitivity, fatigue, adaptation or unrelated variation.",
            ],
            [
                "high_load_equals_injury", "pain_after_load_equals_tissue_damage",
                "low_capacity_equals_structural_pathology", "normal_imaging_equals_normal_load_tolerance",
                "recovery_deficit_proves_causality", "adaptation_state_is_diagnosis",
            ],
        )

    @staticmethod
    def _demand(exposure: LoadExposure) -> float:
        magnitude = exposure.magnitude if exposure.magnitude is not None else 0.5
        duration_factor = min((exposure.duration_minutes or 30) / 120, 1.0)
        frequency_factor = min((exposure.frequency_per_week or 1) / 7, 1.0)
        return min(1.0, 0.6 * magnitude + 0.2 * duration_factor + 0.2 * frequency_factor)

    @staticmethod
    def _capacity(recovery: RecoveryCapacity | None) -> float:
        if recovery is None:
            return 0.5
        values = [v for v in (recovery.current_capacity, recovery.sleep_quality) if v is not None]
        if not values:
            return 0.5
        return max(0.0, min(1.0, sum(values) / len(values)))

    @staticmethod
    def _adaptation(patterns: set[OverloadPattern], responses: list[LoadResponseObservation]) -> AdaptationState:
        if not responses:
            return AdaptationState.UNKNOWN
        worsening = [item for item in responses if (item.symptom_change or 0) > 0]
        improving = [item for item in responses if (item.symptom_change or 0) < 0]
        if OverloadPattern.RECOVERY_DEFICIT in patterns and worsening:
            return AdaptationState.MALADAPTIVE
        if worsening:
            return AdaptationState.INSUFFICIENT
        if improving:
            return AdaptationState.POSITIVE
        return AdaptationState.ADEQUATE

    @staticmethod
    def _effect(branch_id: str, exposure: LoadExposure, effect_type: LoadEvidenceEffectType, strength: str, rationale: str) -> BranchLoadEffect:
        return BranchLoadEffect(branch_id, exposure.id, effect_type, strength, rationale, exposure.provenance, exposure.context_constraints)

    @staticmethod
    def _fallback_provenance(exposures: list[LoadExposure], recovery: RecoveryCapacity | None, responses: list[LoadResponseObservation]) -> list[ProvenanceReference]:
        if exposures:
            return exposures[0].provenance
        if recovery is not None:
            return recovery.provenance
        if responses:
            return responses[0].provenance
        return [ProvenanceReference("FHOS_CURATED", "S08E14", "missing-data-policy")]
