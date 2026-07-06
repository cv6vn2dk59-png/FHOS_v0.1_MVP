"""Application-сервіс Drug Interactions v1.

Interaction Evidence View (docs/SPRINT_5_E01_SUMMARY.md): відповідь
пацієнту складається з трьох незалежних блоків довіри. У v1 сервіс
реалізує лише verified_interaction (дані з Phansalkar 2013) -
patient_note і prescription_history будуть додані окремими сервісами
пізніше, коли з'явиться реальний UI-запит на них, щоб не будувати
структуру наперед (Confirmed Repetition, not Confirmed Intention).
"""
from app.application.uow import UnitOfWork
from app.modules.drug_interactions.domain.entities import (
    DrugInteraction,
    find_interactions,
)
from app.modules.drug_interactions.domain.name_mapping import normalize_drug_name
from app.modules.drug_interactions.domain.phansalkar_2013 import (
    PHANSALKAR_2013_INTERACTIONS,
)
from app.modules.drug_interactions.persistence import mapper
from app.modules.drug_interactions.persistence.orm import DrugInteractionORM
from app.modules.medications.application.service import MedicationService


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
