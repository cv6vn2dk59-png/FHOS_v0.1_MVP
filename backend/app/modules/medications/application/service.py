from sqlalchemy.exc import IntegrityError

from app.application.uow import UnitOfWork
from app.modules.medications.domain.entities import Medication
from app.modules.medications.persistence import mapper
from app.modules.medications.persistence.orm import MedicationORM
from app.modules.medications.schemas.medications import MedicationCreate


class InvalidPatientReferenceError(Exception):
    def __init__(self, patient_profile_id: int):
        self.patient_profile_id = patient_profile_id
        super().__init__(f"Профіль пацієнта з id={patient_profile_id} не існує")


class MedicationService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def create_medication(self, data: MedicationCreate) -> Medication:
        domain_medication = Medication(
            drug_name=data.drug_name,
            start_date=data.start_date,
            patient_profile_id=data.patient_profile_id,
            atc_code=data.atc_code,
            dose_value=data.dose_value,
            dose_unit=data.dose_unit,
            dosage_text=data.dosage_text,
            end_date=data.end_date,
            reason=data.reason,
            notes=data.notes,
        )

        orm_medication = mapper.to_orm(domain_medication)

        try:
            self.uow.repo(MedicationORM).add(orm_medication)
            self.uow.commit()
        except IntegrityError as exc:
            self.uow.rollback()
            if data.patient_profile_id is not None:
                raise InvalidPatientReferenceError(data.patient_profile_id) from exc
            raise

        return mapper.to_domain(orm_medication)

    def list_medications_for_patient(
        self,
        patient_profile_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Medication]:
        repository = self.uow.repo(MedicationORM)
        orm_medications = repository.get_medications_for_patient(
            patient_profile_id=patient_profile_id,
            skip=skip,
            limit=limit,
        )
        return [mapper.to_domain(orm) for orm in orm_medications]