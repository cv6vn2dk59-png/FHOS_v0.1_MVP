from sqlalchemy.exc import IntegrityError

from app.application.uow import UnitOfWork
from app.modules.imaging.domain.entities import ImagingStudy
from app.modules.imaging.persistence import mapper
from app.modules.imaging.persistence.orm import ImagingStudyORM
from app.modules.imaging.schemas.imaging import ImagingStudyCreate


class InvalidPatientReferenceError(Exception):
    def __init__(self, patient_profile_id: int):
        self.patient_profile_id = patient_profile_id
        super().__init__(f"Профіль пацієнта з id={patient_profile_id} не існує")


class ImagingService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def create_study(self, data: ImagingStudyCreate) -> ImagingStudy:
        domain_study = ImagingStudy(
            study_type=data.study_type,
            body_part=data.body_part,
            study_date=data.study_date,
            patient_profile_id=data.patient_profile_id,
            facility_name=data.facility_name,
            radiologist_conclusion=data.radiologist_conclusion,
            image_file_path=data.image_file_path,
            notes=data.notes,
        )

        orm_study = mapper.to_orm(domain_study)

        try:
            self.uow.repo(ImagingStudyORM).add(orm_study)
            self.uow.commit()
        except IntegrityError as exc:
            self.uow.rollback()
            if data.patient_profile_id is not None:
                raise InvalidPatientReferenceError(data.patient_profile_id) from exc
            raise

        return mapper.to_domain(orm_study)

    def list_studies_for_patient(
        self,
        patient_profile_id: int,
        study_type: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[ImagingStudy]:
        repository = self.uow.repo(ImagingStudyORM)
        orm_studies = repository.get_studies_for_patient(
            patient_profile_id=patient_profile_id,
            study_type=study_type,
            skip=skip,
            limit=limit,
        )
        return [mapper.to_domain(orm) for orm in orm_studies]