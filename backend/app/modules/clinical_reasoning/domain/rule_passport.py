"""Паспорт клінічного правила -- FHOS-RULE-R-11 (S08E14R1).

Джерело рішень (FHOS_Master_Working.xlsx, аркуш «Правила реалізації»,
APPROVED 16.07.2026 -- owner_decision=yes):

- FHOS-RULE-R-11 «Паспорт клінічного правила»: кожне правило має rule_id,
  версію, статус, source_type, evidence_strength, обмеження. Довіра до
  кожного правила видима, а не мовчазна (узгоджено з FHOS-DEC-3-3).
- FHOS-RULE-R-14 «Поріг закриття небезпечної гілки»: гілка гіпотези
  закривається тільки при evidence_strength не нижче визначеного порогу
  або підтвердженні лікаря (операціоналізує інваріант 8, FHOS-DEC-2-2).

Ця сутність НЕ дублює EvidenceSource/HypothesisEvidence (domain/evidence.py):
EvidenceSource описує одне джерело доказів; RulePassport описує КЛІНІЧНЕ
ПРАВИЛО системи (напр. правило генерації гіпотези, правило інтерпретації
лабораторного показника, правило закриття гілки) -- rule_id тут це
ідентифікатор правила В КОДІ/КОНФІГУРАЦІЇ, не FHOS-RULE-<Код> (те --
governance ID цього ADR-рішення, а не паспортизованого клінічного правила).

R-14 формалізує вже наявний у коді вільний текстовий скаляр
HypothesisBranch.evidence_strength (domain/hypothesis_expansion.py) --
без зміни його типу (рядок лишається рядком: FHOS-RULE-R-13, backfill
формату без зміни медичного змісту). Реальні значення, які вже
використовуються продюсерами гілок (mechanistic_clustering.py,
biomechanics.py, hypothesis_expansion.py): "speculative", "plausible",
"supported" -- саме вони впорядковані нижче. Невідоме значення отримує
ранг -1 (нижче за "speculative") -- безпечний дефолт: невідома сила
доказів ніколи мовчки не проходить поріг.
"""
from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime

from .evidence import EvidenceSourceType, EvidenceStrength


class RulePassportStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    RETIRED = "retired"


@dataclass
class RulePassport:
    """Паспорт одного клінічного правила (FHOS-RULE-R-11).

    Backfill-правило (FHOS-RULE-R-13): створення паспорта для вже
    існуючого правила -- це технічне оформлення, воно НЕ змінює медичний
    зміст самого правила. Якщо існуюче правило виявляється сумнівним під
    час паспортизації -- це фіксується в limitations як відоме обмеження,
    а не виправляється мовчки в цьому ж кроці.
    """

    rule_id: str
    version: str
    title: str
    status: RulePassportStatus
    source_type: EvidenceSourceType
    evidence_strength: EvidenceStrength
    limitations: list[str] = field(default_factory=list)
    id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.rule_id.strip():
            raise ValueError("rule_id не може бути порожнім")
        if not self.version.strip():
            raise ValueError("version не може бути порожньою")
        if not self.title.strip():
            raise ValueError("title не може бути порожнім")
        if self.status == RulePassportStatus.ACTIVE and self.evidence_strength == EvidenceStrength.UNRATED:
            raise ValueError(
                f"Правило '{self.rule_id}': статус ACTIVE несумісний з "
                "evidence_strength=UNRATED -- довіра має бути видимою "
                "(FHOS-DEC-3-3), а не мовчазною"
            )


# --- FHOS-RULE-R-14: шкала доказів для закриття небезпечної гілки --------

BRANCH_EVIDENCE_STRENGTH_ORDER: dict[str, int] = {
    "speculative": 0,
    "plausible": 1,
    "supported": 2,
}

#: За замовчуванням гілка вважається достатньо доказовою для закриття,
#: якщо evidence_strength >= "supported". Викликач може передати інший
#: поріг явно -- цей дефолт лише safe default, не жорстко закодована
#: медична позиція.
DEFAULT_DANGEROUS_BRANCH_CLOSURE_THRESHOLD = "supported"


def branch_evidence_rank(evidence_strength: str) -> int:
    """Ранг рядкового evidence_strength гілки. Невідоме значення -> -1
    (нижче за будь-яке відоме значення шкали, ніколи не проходить поріг
    мовчки)."""
    return BRANCH_EVIDENCE_STRENGTH_ORDER.get(evidence_strength, -1)


def meets_closure_threshold(
    evidence_strength: str,
    clinician_confirmed: bool,
    threshold: str = DEFAULT_DANGEROUS_BRANCH_CLOSURE_THRESHOLD,
) -> bool:
    """FHOS-RULE-R-14: чи можна закрити гілку -- лише якщо evidence_strength
    сягає порогу АБО лікар явно підтвердив закриття (clinician_confirmed).
    Підтвердження лікаря завжди має пріоритет над автоматичним порогом --
    людина залишається останньою інстанцією (FHOS-DEC-3-1)."""
    if clinician_confirmed:
        return True
    return branch_evidence_rank(evidence_strength) >= branch_evidence_rank(threshold)
