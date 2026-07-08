from sqlalchemy import select

from app.modules.drug_interactions.persistence.orm import (
    DrugInteractionORM,
    PatientInteractionNoteORM,
)
from app.repositories.base import BaseRepository
from app.repositories.registry import RepositoryRegistry


class DrugInteractionRepository(BaseRepository[DrugInteractionORM]):
    def get_all(self) -> list[DrugInteractionORM]:
        statement = select(self.model)
        return list(self.db.execute(statement).scalars().all())


class PatientInteractionNoteRepository(BaseRepository[PatientInteractionNoteORM]):
    def get_notes_for_patient(
        self, patient_profile_id: int | None
    ) -> list[PatientInteractionNoteORM]:
        statement = (
            select(self.model)
            .where(self.model.patient_profile_id == patient_profile_id)
            .order_by(self.model.created_at.desc())
        )
        return list(self.db.execute(statement).scalars().all())


RepositoryRegistry.register(DrugInteractionORM, DrugInteractionRepository)
RepositoryRegistry.register(PatientInteractionNoteORM, PatientInteractionNoteRepository)
