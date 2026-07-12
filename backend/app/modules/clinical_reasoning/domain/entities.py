"""Clinical Reasoning Graph v1 -- domain layer.

Джерело: SPEC_CLINICAL_REASONING_GRAPH.md, розділ 13 (MVP scope) +
Додаток A (ClinicalHypothesis, формальні правила).

КРИТИЧНО (User Echo Prohibition, Додаток A розділ 6.3): кожна
гіпотеза МАЄ поле origin (USER_SUPPLIED / SYSTEM_GENERATED).
find_possible_causes() зобов'язаний повернути хоча б одну
SYSTEM_GENERATED гіпотезу, якщо на вхід подано USER_SUPPLIED --
інакше порушується Hypothesis Expansion Rule (система не має права
просто повторити причину, яку вже назвав користувач).
"""
from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime


class HypothesisOrigin(str, enum.Enum):
    USER_SUPPLIED = "user_supplied"
    SYSTEM_GENERATED = "system_generated"


class HypothesisStatus(str, enum.Enum):
    CANDIDATE = "candidate_hypotheses"  # Diagnostic Boundary Rule -- ніколи не DIAGNOSIS
    VERIFIED = "verified"
    REJECTED = "rejected"


class EvidenceLevel(str, enum.Enum):
    LEVEL_1 = "clinical_guidelines"       # ESC/ADA/ATA/EAU
    LEVEL_2 = "systematic_review"          # Cochrane, meta-analysis
    LEVEL_3 = "individual_study"           # RCT
    LEVEL_4 = "case_report"                # Клінічний досвід, конференції


@dataclass
class HealthNode:
    """Вузол решітки: орган, функція, показник, симптом, хвороба,
    препарат, спосіб життя. Посилається на зовнішній ID (HPO/MONDO/
    CHEBI), не вигадує власний -- той самий принцип, що вже
    застосований у Contraindications/Diseases/Medications.
    """

    external_id: str          # напр. "HP:0003077" чи "MONDO:0005044"
    external_source: str      # напр. "HPO", "MONDO", "CHEBI"
    label: str
    node_kind: str             # Organ/Function/Biomarker/Symptom/Disease/Drug/LifestyleFactor
    id: int | None = None

    def __post_init__(self) -> None:
        if not self.external_id.strip():
            raise ValueError("external_id не може бути порожнім")
        if not self.external_source.strip():
            raise ValueError("external_source не може бути порожнім")


@dataclass
class ClinicalHypothesis:
    """Одна незалежна причинна гілка для симптому/показника.

    Independence Rule (Додаток A, 6.2): дві гіпотези незалежні, якщо
    відрізняються хоча б за одним із: mechanism, anatomical_source,
    body_system, etiology_category. Просте перефразування -- НЕ нова
    гіпотеза.
    """

    symptom_node_id: str        # external_id вузла-симптому
    title: str
    mechanism: str
    origin: HypothesisOrigin
    evidence_level: EvidenceLevel
    anatomical_source: str | None = None
    body_system: str | None = None
    etiology_category: str | None = None
    verification_questions: list[str] = field(default_factory=list)
    supporting_evidence: list[str] = field(default_factory=list)
    contradicting_evidence: list[str] = field(default_factory=list)
    missing_evidence: list[str] = field(default_factory=list)
    source_ids: list[str] = field(default_factory=list)
    status: HypothesisStatus = HypothesisStatus.CANDIDATE
    id: int | None = None
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise ValueError("title не може бути порожнім")
        if not self.mechanism.strip():
            raise ValueError("mechanism не може бути порожнім")

    def independence_key(self) -> tuple:
        """Independence Rule як перевірюваний ключ -- дві гіпотези з
        однаковим ключем вважаються НЕ незалежними (дублікат/синонім).
        """
        return (
            self.mechanism.strip().lower(),
            (self.anatomical_source or "").strip().lower(),
            (self.body_system or "").strip().lower(),
            (self.etiology_category or "").strip().lower(),
        )


def check_hypothesis_expansion(hypotheses: list[ClinicalHypothesis]) -> list[str]:
    """User Echo Prohibition + Independence Rule як виконувана
    перевірка (не тільки документація). Повертає список порушень,
    порожній список -- усе гаразд.

    Критерії приймання (Додаток A, розділ 9), перевірені тут:
    - гілки не є простими синонімами (Independence Rule);
    - гіпотеза користувача не домінує автоматично (User Echo Prohibition).
    """
    violations: list[str] = []

    if not hypotheses:
        violations.append("Список гіпотез порожній -- Hypothesis Expansion не виконано")
        return violations

    user_supplied = [h for h in hypotheses if h.origin == HypothesisOrigin.USER_SUPPLIED]
    system_generated = [h for h in hypotheses if h.origin == HypothesisOrigin.SYSTEM_GENERATED]

    if user_supplied and not system_generated:
        violations.append(
            "User Echo Prohibition: є USER_SUPPLIED гіпотеза, але жодної "
            "SYSTEM_GENERATED -- система лише повторила причину користувача"
        )

    seen_keys: dict[tuple, str] = {}
    for h in hypotheses:
        key = h.independence_key()
        if key in seen_keys:
            violations.append(
                f"Independence Rule: '{h.title}' має той самий independence_key, "
                f"що й '{seen_keys[key]}' -- імовірний дублікат/синонім, не нова гіпотеза"
            )
        else:
            seen_keys[key] = h.title

    for h in hypotheses:
        if h.status != HypothesisStatus.CANDIDATE and h.origin == HypothesisOrigin.SYSTEM_GENERATED:
            if not h.source_ids:
                violations.append(
                    f"'{h.title}' має статус {h.status.value}, але немає source_ids -- "
                    f"Diagnostic Boundary Rule вимагає джерело перед верифікацією"
                )

    return violations
