"""Application-сервіс Contraindications v1 (ADR-0014 п.4, закриття).

Перевіряє АКТИВНІ (is_active()==True) препарати й хвороби пацієнта проти
відомих протипоказань (MeDIC v1, CHEBI/MONDO). Дзеркалить
DrugInteractionService.check_active_medications() -- той самий патерн:
читає facts з Medications v1 + Diseases v1 (нічого не змінюючи в жодному
з них), нормалізує вільний текст через локальні словники, шукає збіги
через доменну функцію find_contraindications().

ВАЖЛИВА, чесно задокументована межа (ADR-0014, оновлення S07E04, тепер і
тут): normalize_to_chebi() і normalize_to_mondo() -- exact-token-match
проти НАМІРЕНО малих словників (4 речовини, 10 хвороб). Реальний
drug_name/diagnosis_name пацієнта, введений вільним текстом, здебільшого
НЕ матиме збігу -- це не помилка сервісу, а пряме, очікуване наслідок
свідомо мінімального Confirmed-Repetition обсягу обох словників.
check_patient() мовчки відкидає записи без збігу (None від normalize_*),
а не намагається fuzzy-match чи вигадати відповідність -- той самий
принцип, що вже застосований у обох словниках.
"""
from app.application.uow import UnitOfWork
from app.modules.contraindications.domain.disease_mapping import normalize_to_mondo
from app.modules.contraindications.domain.entities import (
    Contraindication,
    find_contraindications,
)
from app.modules.contraindications.persistence import mapper
from app.modules.contraindications.persistence.orm import ContraindicationORM
from app.modules.diseases.application.service import DiseaseService
from app.modules.medications.application.service import MedicationService
from app.shared.drug_identity.substance_mapping import normalize_to_chebi


class ContraindicationService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def _load_known_contraindications(self) -> list[Contraindication]:
        repository = self.uow.repo(ContraindicationORM)
        orm_contraindications = repository.get_all()
        return [mapper.to_domain(orm) for orm in orm_contraindications]

    def check_patient(self, patient_profile_id: int) -> list[Contraindication]:
        """Знаходить відомі протипоказання серед АКТИВНИХ препаратів і
        АКТИВНИХ хвороб пацієнта (is_active()==True на сьогодні для обох
        -- лише поточний стан, не історія, на відміну від
        DrugInteractionService.find_prescription_history()).
        """
        medication_service = MedicationService(self.uow)
        medications = medication_service.list_medications_for_patient(
            patient_profile_id=patient_profile_id, limit=1000,
        )
        active_substance_chebi_ids = [
            chebi_id
            for m in medications
            if m.is_active()
            for chebi_id in [normalize_to_chebi(m.drug_name)]
            if chebi_id is not None
        ]

        disease_service = DiseaseService(self.uow)
        diseases = disease_service.list_diseases_for_patient(
            patient_profile_id=patient_profile_id, limit=1000,
        )
        active_disease_mondo_ids = [
            mondo_id
            for d in diseases
            if d.is_active()
            for mondo_id in [normalize_to_mondo(d.diagnosis_name)]
            if mondo_id is not None
        ]

        known_contraindications = self._load_known_contraindications()
        return find_contraindications(
            active_substance_chebi_ids,
            active_disease_mondo_ids,
            known_contraindications,
        )
