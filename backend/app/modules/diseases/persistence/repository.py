from sqlalchemy import select

from app.modules.diseases.persistence.orm import DiseaseORM
from app.repositories.base import BaseRepository
from app.repositories.registry import RepositoryRegistry


class DiseaseRepository(BaseRepository[DiseaseORM]):
    def get_diseases_for_patient(
        self,
        patient_profile_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> list[DiseaseORM]:
        statement = (
            select(self.model)
            .where(self.model.patient_profile_id == patient_profile_id)
            .order_by(self.model.onset_date.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(self.db.execute(statement).scalars().all())


RepositoryRegistry.register(DiseaseORM, DiseaseRepository)
