import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.application.uow import UnitOfWork
from app.modules.drug_interactions.application.service import (
    DrugInteractionService,
    InvalidPatientReferenceError,
)
import app.modules.drug_interactions.persistence.orm  # noqa: F401
import app.modules.drug_interactions.persistence.repository  # noqa: F401
import app.modules.profile.persistence.orm  # noqa: F401
from app.modules.drug_interactions.schemas.drug_interactions import (
    PatientInteractionNoteCreate,
)
from app.persistence.base import Base


@pytest.fixture
def in_memory_uow():
    engine = create_engine("sqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def _enable_fk(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    return UnitOfWork(session_factory=session_factory)


def make_note_data(**overrides):
    data = dict(
        patient_profile_id=None,
        substance_a="warfarin",
        substance_b="amiodarone",
        note_text="Знайшов інформацію про взаємодію на форумі",
    )
    data.update(overrides)
    return PatientInteractionNoteCreate(**data)


class TestCreatePatientNote:
    def test_creates_note_and_assigns_id(self, in_memory_uow):
        with in_memory_uow as uow:
            service = DrugInteractionService(uow)
            note = service.create_patient_note(make_note_data())

            assert note.id is not None
            assert note.unverified is True
            assert note.created_at is not None

    def test_raises_when_patient_profile_id_does_not_exist(self, in_memory_uow):
        with in_memory_uow as uow:
            service = DrugInteractionService(uow)
            with pytest.raises(InvalidPatientReferenceError):
                service.create_patient_note(make_note_data(patient_profile_id=999))

    def test_raises_when_note_exceeds_schema_length_limit(self):
        with pytest.raises(ValueError):
            make_note_data(note_text="x" * 2001)


class TestSubstanceNormalization:
    def test_normalizes_brand_names_on_creation(self, in_memory_uow):
        with in_memory_uow as uow:
            service = DrugInteractionService(uow)
            note = service.create_patient_note(
                make_note_data(substance_a="варфарин", substance_b="кордарон")
            )

            assert note.substance_a == "warfarin"
            assert note.substance_b == "amiodarone"

    def test_pair_key_matches_across_brand_and_inn_naming(self, in_memory_uow):
        with in_memory_uow as uow:
            service = DrugInteractionService(uow)
            note_via_brand = service.create_patient_note(
                make_note_data(substance_a="варфарин", substance_b="кордарон")
            )
            note_via_inn = service.create_patient_note(
                make_note_data(substance_a="warfarin", substance_b="amiodarone")
            )

            assert note_via_brand.pair_key() == note_via_inn.pair_key()

    def test_raises_when_different_brand_names_normalize_to_same_substance(self, in_memory_uow):
        with in_memory_uow as uow:
            service = DrugInteractionService(uow)
            # "кордарон" і "аміодарон" -- різні написання тієї самої
            # речовини (amiodarone). Нормалізація перед побудовою
            # domain-об'єкта повинна це виявити як self-interaction,
            # навіть якщо сирі рядки, введені пацієнтом, відрізнялись.
            with pytest.raises(ValueError):
                service.create_patient_note(
                    make_note_data(substance_a="кордарон", substance_b="аміодарон")
                )


class TestListPatientNotes:
    def test_lists_notes_for_patient(self, in_memory_uow):
        with in_memory_uow as uow:
            service = DrugInteractionService(uow)
            service.create_patient_note(make_note_data(substance_a="warfarin", substance_b="amiodarone"))
            service.create_patient_note(make_note_data(substance_a="sertraline", substance_b="tranylcypromine"))

            notes = service.list_patient_notes(patient_profile_id=None)

            assert len(notes) == 2

    def test_returns_empty_list_when_no_notes(self, in_memory_uow):
        with in_memory_uow as uow:
            service = DrugInteractionService(uow)
            notes = service.list_patient_notes(patient_profile_id=None)

            assert notes == []

    def test_most_recent_note_first(self, in_memory_uow):
        with in_memory_uow as uow:
            service = DrugInteractionService(uow)
            first = service.create_patient_note(
                make_note_data(substance_a="warfarin", substance_b="amiodarone")
            )
            second = service.create_patient_note(
                make_note_data(substance_a="sertraline", substance_b="tranylcypromine")
            )

            notes = service.list_patient_notes(patient_profile_id=None)

            assert notes[0].id == second.id
            assert notes[1].id == first.id
