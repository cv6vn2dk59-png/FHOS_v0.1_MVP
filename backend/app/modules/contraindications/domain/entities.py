"""Contraindications v1 -- domain-шар.

Facts of "цю речовину не можна призначати при цій хворобі" з зовнішнього
джерела знань (MeDIC v1). Архітектурні рішення зафіксовані в
docs/ADR/ADR-0014-contraindications-v1-domain-scope.md і
docs/SPRINT_7_E01_SUMMARY.md.

Ключові відмінності від Drug Interactions v1:
  - Асиметрична модель: substance і disease -- різні типи сутностей,
    ніколи не можуть помінятись місцями (на відміну від side_a/side_b).
    Тому pair_key() тут не потрібен і не існує.
  - severity відсутня навмисно: MeDIC v1 не надає цих даних. Сам факт
    існування запису Contraindication вже означає протипоказання --
    вигадувати шкалу без джерела означало б Confirmed Intention,
    а не Confirmed Repetition.
  - Ідентифікатори -- CHEBI (речовина) і MONDO (хвороба), усталені
    біомедичні онтології у форматі CURIE ("CHEBI:12345", "MONDO:0005148").
    Це свідомо ІНШИЙ підхід, ніж Medications (drug_name, вільний текст)
    і Diseases (diagnosis_name, вільний текст, ADR-0013). Contraindication
    зберігає CHEBI/MONDO ID як рядок, БЕЗ FK на ще не існуючу таблицю
    active_substances/clinical_moieties -- те саме тимчасове рішення,
    що Drug Interactions v1 мав із name_mapping.py до появи реальної
    інфраструктури.

Явно ПОЗА межами v1 (Confirmed Repetition, not Confirmed Intention):
  - Побудова повної таблиці active_substances/clinical_moieties для
    усіх 3857 препаратів MeDIC (окреме, велике рішення: чи вантажити
    весь Drug List, як валідувати заявлений 71%/29% розкол).
  - Розв'язання Medications.drug_name -> CHEBI і
    Diseases.diagnosis_name -> MONDO -- обидва боки цієї проблеми
    однаково не розв'язані в v1, жоден модуль сьогодні не зберігає
    CHEBI/MONDO. Domain-шар цього не потребує (приймає готові ID),
    але Application-шар не зможе працювати з реальними записами
    пацієнта, поки хоч один бік не матиме мапінгу.
"""
from __future__ import annotations

from dataclasses import dataclass


def _validate_ontology_id(value: str, prefix: str, field_name: str) -> str:
    stripped = value.strip()
    if not stripped:
        raise ValueError(f"{field_name} не може бути порожнім")
    if not stripped.upper().startswith(prefix):
        raise ValueError(
            f"{field_name} повинен починатися з {prefix!r} (отримано {value!r})"
        )
    return stripped


@dataclass
class Contraindication:
    """Факт: речовина (CHEBI) протипоказана при хворобі (MONDO)."""

    substance_chebi_id: str
    disease_mondo_id: str
    description: str
    knowledge_source_id: str
    id: int | None = None

    def __post_init__(self) -> None:
        self.substance_chebi_id = _validate_ontology_id(
            self.substance_chebi_id, "CHEBI:", "substance_chebi_id"
        )
        self.disease_mondo_id = _validate_ontology_id(
            self.disease_mondo_id, "MONDO:", "disease_mondo_id"
        )

    def matches(
        self, substance_chebi_ids: set[str], disease_mondo_ids: set[str]
    ) -> bool:
        """True, якщо і речовина, і хвороба присутні серед фактів пацієнта."""
        return (
            self.substance_chebi_id in substance_chebi_ids
            and self.disease_mondo_id in disease_mondo_ids
        )


def find_contraindications(
    substance_chebi_ids: list[str],
    disease_mondo_ids: list[str],
    known_contraindications: list[Contraindication],
) -> list[Contraindication]:
    """Повертає всі протипоказання, що застосовуються до набору фактів пацієнта."""
    substances = set(substance_chebi_ids)
    diseases = set(disease_mondo_ids)
    return [c for c in known_contraindications if c.matches(substances, diseases)]
