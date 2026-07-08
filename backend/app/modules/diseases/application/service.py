from sqlalchemy.exc import IntegrityError

from app.application.uow import UnitOfWork
from app.modules.diseases.domain.entities import Disease
from app.modules.diseases.persistence import mapper
from app.modules.diseases.persistence.orm import DiseaseORM
from app.modules.diseases.schemas.diseases import DiseaseCreate


class InvalidPatientReferenceError(Exception):
    def __init__(self, patient_profile_id: int):
        self.patient_profile_id = patient_profile_id
        super().__init__(f"Профіль пацієнта з id={patient_profile_id} не існує")


class DiseaseService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def create_disease(self, data: DiseaseCreate) -> Disease:
        domain_disease = Disease(
            diagnosis_name=data.diagnosis_name,
            onset_date=data.onset_date,
            patient_profile_id=data.patient_profile_id,
            icd_code=data.icd_code,
            resolved_date=data.resolved_date,
            notes=data.notes,
        )

        orm_disease = mapper.to_orm(domain_disease)

        try:
            self.uow.repo(DiseaseORM).add(orm_disease)
            self.uow.commit()
        except IntegrityError as exc:
            self.uow.rollback()
            if data.patient_profile_id is not None:
                raise InvalidPatientReferenceError(data.patient_profile_id) from exc
            raise

        return mapper.to_domain(orm_disease)

    def list_diseases_for_patient(
        self,
        patient_profile_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Disease]:
        repository = self.uow.repo(DiseaseORM)
        orm_diseases = repository.get_diseases_for_patient(
            patient_profile_id=patient_profile_id,
            skip=skip,
            limit=limit,
        )
        return [mapper.to_domain(orm) for orm in orm_diseases]
