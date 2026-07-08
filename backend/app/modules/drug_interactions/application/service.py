"""Application-сервіс Drug Interactions v1.

Interaction Evidence View (docs/SPRINT_5_E01_SUMMARY.md): відповідь
пацієнту складається з трьох незалежних блоків довіри. Усі три
реалізовано: verified_interaction (Phansalkar 2013), prescription_history
(перетин у часі за Medications) і patient_note (особиста нотатка,
НЕ перевірена системою -- див. docs/SPRINT_5_E02_SUMMARY.md).
"""
from sqlalchemy.exc import IntegrityError

from app.application.uow import UnitOfWork
from app.modules.drug_interactions.domain.entities import (
    DrugInteraction,
    MedicationRecord,
    PatientInteractionNote,
    PrescriptionHistoryEntry,
    find_historical_overlapping_prescriptions,
    find_interactions,
)
from app.modules.drug_interactions.domain.name_mapping import normalize_drug_name
from app.modules.drug_interactions.domain.phansalkar_2013 import (
    PHANSALKAR_2013_INTERACTIONS,
)
from app.modules.drug_interactions.persistence import mapper
from app.modules.drug_interactions.persistence.orm import (
    DrugInteractionORM,
    PatientInteractionNoteORM,
)
from app.modules.drug_interactions.schemas.drug_interactions import (
    PatientInteractionNoteCreate,
)
from app.modules.medications.application.service import MedicationService


class InvalidPatientReferenceError(Exception):
    def __init__(self, patient_profile_id: int):
        self.patient_profile_id = patient_profile_id
        super().__init__(f"Профіль пацієнта з id={patient_profile_id} не існує")


class DrugInteractionService:
    """Перевірка взаємодій між препаратами, які пацієнт приймає зараз.

    Джерело даних про взаємодії: repository (БД), заповнена з
    PHANSALKAR_2013_INTERACTIONS при seed-і (див. seed_phansalkar_data.py).
    Якщо repository порожній (seed ще не виконано) - сервіс тихо falls
    back на дані напряму з phansalkar_2013.py, щоб застосунок працював
    навіть без seed-кроку у v1.
    """

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def _load_known_interactions(self) -> list[DrugInteraction]:
        repository = self.uow.repo(DrugInteractionORM)
        orm_interactions = repository.get_all()
        if orm_interactions:
            return [mapper.to_domain(orm) for orm in orm_interactions]
        return PHANSALKAR_2013_INTERACTIONS

    def check_active_medications(self, patient_profile_id: int) -> list[DrugInteraction]:
        """Знаходить відомі взаємодії серед препаратів, які пацієнт
        приймає ЗАРАЗ (is_active() == True на сьогодні).
        """
        medication_service = MedicationService(self.uow)
        medications = medication_service.list_medications_for_patient(
            patient_profile_id=patient_profile_id, limit=1000,
        )

        active_substances = [
            normalize_drug_name(m.drug_name) for m in medications if m.is_active()
        ]

        known_interactions = self._load_known_interactions()
        return find_interactions(active_substances, known_interactions)

    def find_prescription_history(self, patient_profile_id: int) -> list[PrescriptionHistoryEntry]:
        """Interaction Evidence View, блок prescription_history:
        історичний факт спільного призначення (перетин у часі), НЕ
        доказ безпеки. Дивиться на ВСЮ історію Medications (не тільки
        активні, на відміну від check_active_medications()).
        """
        medication_service = MedicationService(self.uow)
        medications = medication_service.list_medications_for_patient(
            patient_profile_id=patient_profile_id, limit=1000,
        )

        records = [
            MedicationRecord(
                drug_name=m.drug_name,
                substance=normalize_drug_name(m.drug_name),
                start_date=m.start_date,
                end_date=m.end_date,
            )
            for m in medications
        ]

        known_interactions = self._load_known_interactions()
        return find_historical_overlapping_prescriptions(records, known_interactions)

    def create_patient_note(self, data: PatientInteractionNoteCreate) -> PatientInteractionNote:
        """Interaction Evidence View, блок patient_note: особиста нотатка
        пацієнта про взаємодію двох речовин. unverified=True завжди --
        доменна модель (PatientInteractionNote) не дає створити інакше.
        """
        domain_note = PatientInteractionNote(
            patient_profile_id=data.patient_profile_id,
            substance_a=data.substance_a,
            substance_b=data.substance_b,
            note_text=data.note_text,
        )

        orm_note = mapper.note_to_orm(domain_note)

        try:
            self.uow.repo(PatientInteractionNoteORM).add(orm_note)
            self.uow.commit()
        except IntegrityError as exc:
            self.uow.rollback()
            if data.patient_profile_id is not None:
                raise InvalidPatientReferenceError(data.patient_profile_id) from exc
            raise

        return mapper.note_to_domain(orm_note)

    def list_patient_notes(self, patient_profile_id: int | None) -> list[PatientInteractionNote]:
        """Усі нотатки пацієнта про взаємодії (усі пари речовин).
        Фільтрація за конкретною парою через pair_key() лишається на
        боці споживача, коли з'явиться конкретна потреба.
        """
        repository = self.uow.repo(PatientInteractionNoteORM)
        orm_notes = repository.get_notes_for_patient(patient_profile_id)
        return [mapper.note_to_domain(orm) for orm in orm_notes]
