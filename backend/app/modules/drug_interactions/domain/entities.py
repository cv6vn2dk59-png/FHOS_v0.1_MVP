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


@dataclass
class MedicationRecord:
    """Мінімальні дані про призначення, потрібні для overlap-перевірки.
    Заповнюється application-шаром з Medications, substance -- вже
    нормалізована назва (через name_mapping.normalize_drug_name).
    """

    drug_name: str
    substance: str
    start_date: "date"
    end_date: "date | None" = None


@dataclass
class PrescriptionHistoryEntry:
    """Історичний факт: два препарати з відомою взаємодією приймались
    одночасно (overlap у часі). НЕ доказ безпеки чи небезпеки -- лише
    факт спільного призначення. warning є обов'язковою частиною
    response object, не текстом на фронтенді (рішення Devil Review).
    """

    medication_a_name: str
    medication_b_name: str
    substance_a: str
    substance_b: str
    medication_a_start_date: "date"
    medication_a_end_date: "date | None"
    medication_b_start_date: "date"
    medication_b_end_date: "date | None"
    overlap_start: "date"
    overlap_end: "date"
    warning: str = "Historical co-prescription is not proof of safety."


def find_historical_overlapping_prescriptions(
    records: list["MedicationRecord"],
    known_interactions: list["DrugInteraction"],
    as_of=None,
) -> list["PrescriptionHistoryEntry"]:
    """Знаходить пари препаратів з відомою взаємодією, чиї періоди
    прийому перетинались у часі. end_date=None означає "триває
    дотепер" (as_of, за замовчуванням -- сьогодні), а не ігнорується.
    """
    import datetime as _dt

    reference_date = as_of if as_of is not None else _dt.date.today()
    entries: list[PrescriptionHistoryEntry] = []

    for i in range(len(records)):
        for j in range(i + 1, len(records)):
            a, b = records[i], records[j]
            if _normalize(a.substance) == _normalize(b.substance):
                continue
            if not any(
                interaction.matches({a.substance, b.substance})
                for interaction in known_interactions
            ):
                continue

            a_end = a.end_date if a.end_date is not None else reference_date
            b_end = b.end_date if b.end_date is not None else reference_date

            overlap_start = max(a.start_date, b.start_date)
            overlap_end = min(a_end, b_end)
            if overlap_start > overlap_end:
                continue

            entries.append(
                PrescriptionHistoryEntry(
                    medication_a_name=a.drug_name,
                    medication_b_name=b.drug_name,
                    substance_a=a.substance,
                    substance_b=b.substance,
                    medication_a_start_date=a.start_date,
                    medication_a_end_date=a.end_date,
                    medication_b_start_date=b.start_date,
                    medication_b_end_date=b.end_date,
                    overlap_start=overlap_start,
                    overlap_end=overlap_end,
                )
            )

    return entries


MAX_PATIENT_NOTE_LENGTH = 2000


@dataclass
class PatientInteractionNote:
    """Особиста нотатка пацієнта про взаємодію двох речовин.

    НЕ перевірена системою -- джерело може бути будь-яким (пошук в
    інтернеті, порада знайомого тощо). Обов'язково показується з
    позначкою "не перевірено", ніколи не змішується з
    verified_interactions чи prescription_history (Architect Session,
    S05E01: "Interaction Evidence View").
    """

    patient_profile_id: "int | None"
    substance_a: str
    substance_b: str
    note_text: str
    id: "int | None" = None
    created_at: "object" = None
    unverified: bool = True

    def __post_init__(self) -> None:
        if not self.note_text or not self.note_text.strip():
            raise ValueError("Текст нотатки не може бути порожнім")
        if len(self.note_text) > MAX_PATIENT_NOTE_LENGTH:
            raise ValueError(
                f"Нотатка перевищує ліміт {MAX_PATIENT_NOTE_LENGTH} символів "
                f"(зараз {len(self.note_text)})"
            )
        if _normalize(self.substance_a) == _normalize(self.substance_b):
            raise ValueError("substance_a і substance_b не можуть збігатися")

    def pair_key(self) -> tuple[str, str]:
        """Той самий принцип симетрії, що й у DrugInteraction: порядок
        введення речовин не має значення для пошуку нотатки.
        """
        return tuple(sorted([_normalize(self.substance_a), _normalize(self.substance_b)]))
