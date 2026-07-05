from sqlalchemy import select

from app.modules.medications.persistence.orm import MedicationORM
from app.repositories.base import BaseRepository
from app.repositories.registry import RepositoryRegistry


class MedicationRepository(BaseRepository[MedicationORM]):
    def get_medications_for_patient(
        self,
        patient_profile_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> list[MedicationORM]:
        statement = (
            select(self.model)
            .where(self.model.patient_profile_id == patient_profile_id)
            .order_by(self.model.start_date.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(self.db.execute(statement).scalars().all())


RepositoryRegistry.register(MedicationORM, MedicationRepository)