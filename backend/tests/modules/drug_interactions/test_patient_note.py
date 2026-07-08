import pytest

from app.modules.drug_interactions.domain.entities import (
    MAX_PATIENT_NOTE_LENGTH,
    PatientInteractionNote,
)


def make_note(note_text="Знайшов інформацію про взаємодію на форумі", substance_a="warfarin", substance_b="amiodarone"):
    return PatientInteractionNote(
        patient_profile_id=1,
        substance_a=substance_a,
        substance_b=substance_b,
        note_text=note_text,
    )


class TestValidation:
    def test_raises_when_note_text_empty(self):
        with pytest.raises(ValueError):
            make_note(note_text="")

    def test_raises_when_note_text_whitespace_only(self):
        with pytest.raises(ValueError):
            make_note(note_text="   ")

    def test_raises_when_note_exceeds_max_length(self):
        with pytest.raises(ValueError):
            make_note(note_text="x" * (MAX_PATIENT_NOTE_LENGTH + 1))

    def test_allows_note_at_exactly_max_length(self):
        note = make_note(note_text="x" * MAX_PATIENT_NOTE_LENGTH)
        assert len(note.note_text) == MAX_PATIENT_NOTE_LENGTH

    def test_raises_when_substances_are_the_same(self):
        with pytest.raises(ValueError):
            make_note(substance_a="warfarin", substance_b="Warfarin")


class TestDefaults:
    def test_unverified_is_always_true(self):
        note = make_note()
        assert note.unverified is True


class TestPairKeySymmetry:
    def test_pair_key_same_regardless_of_order(self):
        n1 = make_note(substance_a="warfarin", substance_b="amiodarone")
        n2 = make_note(substance_a="amiodarone", substance_b="warfarin")
        assert n1.pair_key() == n2.pair_key()

    def test_pair_key_case_insensitive(self):
        n1 = make_note(substance_a="Warfarin", substance_b="Amiodarone")
        n2 = make_note(substance_a="warfarin", substance_b="amiodarone")
        assert n1.pair_key() == n2.pair_key()
