"""Drug Interactions v1 -- препарат ↔ препарат.

Scope, Canonical Identifier, Symmetry Rule, Combination Drugs -- рішення
задокументовані в docs/SPRINT_5_E01_SUMMARY.md та ADR-0012.

ВАЖЛИВО: сторони взаємодії -- це КЛАСИ речовин (наприклад "інгібітори МАО"
включає кілька окремих речовин), не одна речовина. Джерело Phansalkar 2013
визначає взаємодії саме на рівні класів, тому DrugInteraction.side_a і
side_b -- списки речовин, а не окремі рядки.
"""
from __future__ import annotations

import enum
from dataclasses import dataclass


class InteractionSeverity(str, enum.Enum):
    CONTRAINDICATED = "contraindicated"


def _normalize(name: str) -> str:
    return name.strip().lower()


@dataclass
class DrugInteraction:
    """Факт відомої взаємодії між двома класами речовин.

    Symmetry Rule: A+B і B+A -- одна й та сама взаємодія. pair_key()
    повертає відсортовану пару множин речовин, незалежно від того,
    в якому порядку side_a/side_b передані при створенні.
    """

    side_a: list[str]
    side_b: list[str]
    severity: InteractionSeverity
    description: str
    knowledge_source_id: str
    id: int | None = None

    def __post_init__(self) -> None:
        if not self.side_a or not self.side_b:
            raise ValueError(
                "DrugInteraction повинен мати хоча б одну речовину з кожного боку"
            )
        normalized_a = {_normalize(s) for s in self.side_a}
        normalized_b = {_normalize(s) for s in self.side_b}
        if normalized_a & normalized_b:
            raise ValueError(
                "side_a і side_b не можуть мати спільні речовини "
                "(взаємодія речовини сама з собою не має сенсу)"
            )

    def pair_key(self) -> tuple[frozenset[str], frozenset[str]]:
        """Ключ для симетричного пошуку -- не залежить від порядку side_a/side_b."""
        a = frozenset(_normalize(s) for s in self.side_a)
        b = frozenset(_normalize(s) for s in self.side_b)
        return tuple(sorted([a, b], key=lambda s: sorted(s)))

    def matches(self, substances: set[str]) -> bool:
        """Чи присутня хоча б одна речовина з КОЖНОГО боку серед `substances`."""
        normalized = {_normalize(s) for s in substances}
        a = {_normalize(s) for s in self.side_a}
        b = {_normalize(s) for s in self.side_b}
        return bool(a & normalized) and bool(b & normalized)


def find_interactions(
    substances: list[str], known_interactions: list[DrugInteraction]
) -> list[DrugInteraction]:
    """Знаходить усі відомі взаємодії серед списку речовин пацієнта."""
    substance_set = set(substances)
    return [i for i in known_interactions if i.matches(substance_set)]
