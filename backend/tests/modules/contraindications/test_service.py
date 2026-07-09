"""ContraindicationService.check_patient() -- перевірка Application-шару.

CHEBI:10033/MONDO:0005044 (warfarin/hypertension) -- вигаданий тестовий
Contraindication-фікстур, НЕ реальний клінічний факт з MeDIC (той самий
підхід, що вже в test_persistence.py: metformin+ниркова недостатність).
Реальні MeDIC-записи перевіряються окремо через seed-скрипт і реальний
venv, не тут -- тут перевіряється лише логіка сервісу (нормалізація +
фільтр активності + пошук збігів), на контрольованих literal-значеннях.
"""
from datetime import date

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.application.uow import UnitOfWork
from app.modules.contraindications.application.service import ContraindicationService
from app.modules.contraindications.domain.entities import Contraindication
from app.modules.contraindications.persistence import mapper
from app.modules.contraindications.persistence.orm import ContraindicationORM  # noqa: F401
import app.modules.contraindications.persistence.repository  # noqa: F401
from app.modules.diseases.application.service import DiseaseService
from app.modules.diseases.persistence.orm import DiseaseORM  # noqa: F401
import app.modules.diseases.persistence.repository  # noqa: F401
from app.modules.diseases.schemas.diseases import DiseaseCreate
from app.modules.medications.application.service import MedicationService
from app.modules.medications.persistence.orm import MedicationORM  # noqa: F401
import app.modules.medications.persistence.repository  # noqa: F401
from app.modules.medications.schemas.medications import MedicationCreate
import app.modules.profile.persistence.orm  # noqa: F401
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


def seed_contraindication(uow: UnitOfWork, chebi_id: str, mondo_id: str) -> None:
    uow.repo(ContraindicationORM).add(mapper.to_orm(Contraindication(
        substance_chebi_id=chebi_id,
        disease_mondo_id=mondo_id,
        description="тестовий фікстур, не реальний клінічний факт",
        knowledge_source_id="test",
    )))
    uow.commit()


def create_medication(service: MedicationService, drug_name: str, day: int, end_day: int | None = None) -> None:
    service.create_medication(
        MedicationCreate(
            drug_name=drug_name,
            start_date=date(2026, 1, day),
            end_date=date(2026, 1, end_day) if end_day else None,
            patient_profile_id=None,
        )
    )


def create_disease(
    service: DiseaseService, diagnosis_name: str, day: int, resolved_day: int | None = None
) -> None:
    service.create_disease(
        DiseaseCreate(
            diagnosis_name=diagnosis_name,
            onset_date=date(2026, 1, day),
            resolved_date=date(2026, 1, resolved_day) if resolved_day else None,
            patient_profile_id=None,
        )
    )


class TestCheckPatientFindsKnownContraindication:
    def test_finds_contraindication_between_active_medication_and_active_disease(
        self, in_memory_uow
    ):
        with in_memory_uow as uow:
            seed_contraindication(uow, "CHEBI:10033", "MONDO:0005044")

            create_medication(MedicationService(uow), "warfarin", day=1)
            create_disease(DiseaseService(uow), "гіпертонія", day=1)

            service = ContraindicationService(uow)
            result = service.check_patient(patient_profile_id=None)

            assert len(result) == 1
            assert result[0].substance_chebi_id == "CHEBI:10033"
            assert result[0].disease_mondo_id == "MONDO:0005044"

    def test_normalizes_ukrainian_brand_name_and_alternate_disease_form(self, in_memory_uow):
        """варфарин (укр. брендова назва) -> CHEBI:10033 через
        normalize_to_chebi(); "артеріальна гіпертензія" (друга форма
        запису) -> той самий MONDO:0005044, що й "гіпертонія"."""
        with in_memory_uow as uow:
            seed_contraindication(uow, "CHEBI:10033", "MONDO:0005044")

            create_medication(MedicationService(uow), "варфарин", day=1)
            create_disease(DiseaseService(uow), "артеріальна гіпертензія", day=1)

            service = ContraindicationService(uow)
            result = service.check_patient(patient_profile_id=None)

            assert len(result) == 1


class TestCheckPatientFindsNothing:
    def test_no_match_when_no_known_contraindication(self, in_memory_uow):
        with in_memory_uow as uow:
            create_medication(MedicationService(uow), "warfarin", day=1)
            create_disease(DiseaseService(uow), "гіпертонія", day=1)

            service = ContraindicationService(uow)
            result = service.check_patient(patient_profile_id=None)

            assert result == []

    def test_ignores_medication_that_is_no_longer_active(self, in_memory_uow):
        with in_memory_uow as uow:
            seed_contraindication(uow, "CHEBI:10033", "MONDO:0005044")

            create_medication(MedicationService(uow), "warfarin", day=1, end_day=5)
            create_disease(DiseaseService(uow), "гіпертонія", day=1)

            service = ContraindicationService(uow)
            result = service.check_patient(patient_profile_id=None)

            assert result == []

    def test_ignores_resolved_disease(self, in_memory_uow):
        with in_memory_uow as uow:
            seed_contraindication(uow, "CHEBI:10033", "MONDO:0005044")

            create_medication(MedicationService(uow), "warfarin", day=1)
            create_disease(DiseaseService(uow), "гіпертонія", day=1, resolved_day=5)

            service = ContraindicationService(uow)
            result = service.check_patient(patient_profile_id=None)

            assert result == []

    def test_ignores_drug_name_absent_from_starter_dictionary(self, in_memory_uow):
        """ібупрофен -- реальний, поширений препарат, свідомо відсутній
        у SUBSTANCE_TO_CHEBI (4 речовини, Confirmed Repetition). Не
        помилка -- очікувана межа v1, задокументована в docstring
        service.py."""
        with in_memory_uow as uow:
            seed_contraindication(uow, "CHEBI:10033", "MONDO:0005044")

            create_medication(MedicationService(uow), "ібупрофен", day=1)
            create_disease(DiseaseService(uow), "гіпертонія", day=1)

            service = ContraindicationService(uow)
            result = service.check_patient(patient_profile_id=None)

            assert result == []

    def test_ignores_diagnosis_name_absent_from_starter_dictionary(self, in_memory_uow):
        """панкреатит -- свідомо відсутній у DISEASE_TO_MONDO (10 хвороб,
        Confirmed Repetition). Та сама очікувана межа."""
        with in_memory_uow as uow:
            seed_contraindication(uow, "CHEBI:10033", "MONDO:0005044")

            create_medication(MedicationService(uow), "warfarin", day=1)
            create_disease(DiseaseService(uow), "панкреатит", day=1)

            service = ContraindicationService(uow)
            result = service.check_patient(patient_profile_id=None)

            assert result == []


class TestCheckPatientNoData:
    def test_returns_empty_list_when_patient_has_no_medications_or_diseases(self, in_memory_uow):
        with in_memory_uow as uow:
            seed_contraindication(uow, "CHEBI:10033", "MONDO:0005044")

            service = ContraindicationService(uow)
            result = service.check_patient(patient_profile_id=None)

            assert result == []
