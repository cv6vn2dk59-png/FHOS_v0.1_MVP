"""ICD-11 v1 -- domain-шар.

Статичний WHO Linearization знання-актив: ієрархія Chapter -> Block ->
Category. Джерело v1 -- підготовлений Excel-файл (тестова підмножина,
розділ 1), НЕ живий виклик ICD-API ВООЗ і НЕ PDF (ліцензія ICD-11:
CC BY-NC-ND, No Derivatives -- деталі задокументувати окремо в
PROJECT_STATE.md, розділ ICD-11).

id -- НЕ синтетичний DB-серіал (на відміну від інших сутностей
проекту, де id: int | None = None призначається базою даних). Тут
id -- це реальний WHO Linearization URI або blockId, обов'язковий
параметр конструктора з першого дня, оскільки саме він визначає
ідентичність вузла в дереві (parent_id посилається на нього ж).

Валідація: тільки id не порожній -- жорстко. Зв'язок
node_kind/icd_code (категорії зазвичай мають icd_code, блоки й глави
можуть його не мати) -- це опис форми реальних WHO-даних, НЕ жорсткий
constraint: реальні дані можуть мати винятки (напр. блок із діапазоном
кодів), і штучна заборона тут ризикує відкидати легітимні записи
без підтвердженого джерела такого правила (Confirmed Repetition, not
Confirmed Intention).

Явно поза межами v1 (ADR-0015):
  - Universal Clinical Classification Layer -- відхилено (Second
    Consumer Rule: немає другого реального класифікатора в проекті,
    що потребував би спільної абстракції).
  - Живий виклик ICD-API ВООЗ -- не зараз, статичний імпорт.
  - Повне дерево 17000+ вузлів -- v1 обмежується розділом 1
    (тестова підмножина), розширення -- окреме майбутнє рішення.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class TranslationStatus(str, Enum):
    VERIFIED = "verified"
    AUTO_IMPORTED = "auto_imported"
    NEEDS_REVIEW = "needs_review"
    MISSING = "missing"


class NodeKind(str, Enum):
    """Дзеркалить офіційний WHO class_kind."""

    CHAPTER = "chapter"
    BLOCK = "block"
    CATEGORY = "category"


class SpecialCode(str, Enum):
    NONE = "none"
    Y = "y"
    Z = "z"


@dataclass
class ICD11Node:
    """Вузол WHO Linearization дерева (Chapter/Block/Category)."""

    id: str
    english_title: str
    translation_status: TranslationStatus
    node_kind: NodeKind
    special_code: SpecialCode
    sort_order: int
    source_release: str
    parent_id: str | None = None
    icd_code: str | None = None
    ukrainian_title: str | None = None

    def __post_init__(self) -> None:
        if not self.id or not self.id.strip():
            raise ValueError(
                "id не може бути порожнім (очікується WHO Linearization URI або blockId)"
            )

    def is_root(self) -> bool:
        """True для кореневого вузла (Chapter без parent_id)."""
        return self.parent_id is None
