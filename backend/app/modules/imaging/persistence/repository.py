from sqlalchemy import select

from app.modules.imaging.persistence.orm import ImagingStudyORM
from app.repositories.base import BaseRepository
from app.repositories.registry import RepositoryRegistry


class ImagingStudyRepository(BaseRepository[ImagingStudyORM]):
    def get_studies_for_patient(
        self,
        patient_profile_id: int,
        study_type: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[ImagingStudyORM]:
        statement = (
            select(self.model)
            .where(self.model.patient_profile_id == patient_profile_id)
            .order_by(self.model.study_date.desc())
            .offset(skip)
            .limit(limit)
        )
        if study_type is not None:
            statement = statement.where(self.model.study_type == study_type)
        return list(self.db.execute(statement).scalars().all())


RepositoryRegistry.register(ImagingStudyORM, ImagingStudyRepository)