from __future__ import annotations

import enum
from dataclasses import dataclass, field


class ObservationClass(str, enum.Enum):
    WITHIN_REFERENCE = "within_reference"
    OUTSIDE_REFERENCE = "outside_reference"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class EvidenceRole(str, enum.Enum):
    SIGNAL = "signal"
    CONTEXT = "context"
    NEUTRAL = "neutral"


@dataclass(frozen=True)
class LaboratoryObservationSnapshot:
    laboratory_result_id: int
    patient_id: str
    episode_id: str
    node_id: str
    test_code: str
    test_name: str
    value: float | None
    unit: str | None
    reference_min: float | None
    reference_max: float | None
    critical_low: float | None
    critical_high: float | None
    interpretation: str
    observation_class: ObservationClass
    evidence_role: EvidenceRole
    result_date: str | None
    provenance: dict[str, str | int | None] = field(default_factory=dict)


@dataclass(frozen=True)
class ReviewDomain:
    code: str
    title: str
    status: str
    evidence_result_ids: list[int]
    signal_result_ids: list[int]
    context_result_ids: list[int]


LAB_REVIEW_DOMAINS: dict[str, tuple[str, set[str]]] = {
    "glycemic_regulation": (
        "Глікемічна регуляція",
        {"GLUCOSE_FASTING", "HBA1C", "INSULIN_FASTING"},
    ),
    "lipid_metabolism": (
        "Ліпідний обмін",
        {"TRIGLYCERIDES", "LDL", "HDL", "TOTAL_CHOLESTEROL", "APOB"},
    ),
    "hepatic_context": (
        "Печінковий контекст",
        {"ALT", "AST", "GGT", "ALP", "BILIRUBIN_TOTAL"},
    ),
    "renal_context": (
        "Нирковий контекст",
        {"CREATININE", "EGFR", "UREA", "ALBUMIN_URINE"},
    ),
}


def classify_observation(interpretation: str) -> tuple[ObservationClass, EvidenceRole]:
    if interpretation in {"critical_low", "critical_high"}:
        return ObservationClass.CRITICAL, EvidenceRole.SIGNAL
    if interpretation in {"low", "high"}:
        return ObservationClass.OUTSIDE_REFERENCE, EvidenceRole.SIGNAL
    if interpretation == "normal":
        return ObservationClass.WITHIN_REFERENCE, EvidenceRole.CONTEXT
    return ObservationClass.UNKNOWN, EvidenceRole.NEUTRAL


def build_review_domains(observations: list[LaboratoryObservationSnapshot]) -> list[ReviewDomain]:
    result: list[ReviewDomain] = []
    by_code = {observation.test_code.upper(): observation for observation in observations}

    for domain_code, (title, test_codes) in LAB_REVIEW_DOMAINS.items():
        domain_observations = [by_code[code] for code in test_codes if code in by_code]
        if not domain_observations:
            continue

        signal_ids = [
            observation.laboratory_result_id
            for observation in domain_observations
            if observation.evidence_role == EvidenceRole.SIGNAL
        ]
        context_ids = [
            observation.laboratory_result_id
            for observation in domain_observations
            if observation.evidence_role != EvidenceRole.SIGNAL
        ]
        status = "attention" if signal_ids else "context_only"
        result.append(
            ReviewDomain(
                code=domain_code,
                title=title,
                status=status,
                evidence_result_ids=[observation.laboratory_result_id for observation in domain_observations],
                signal_result_ids=signal_ids,
                context_result_ids=context_ids,
            )
        )

    return result
