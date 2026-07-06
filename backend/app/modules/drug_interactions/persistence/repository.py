from sqlalchemy import select

from app.modules.drug_interactions.persistence.orm import DrugInteractionORM
from app.repositories.base import BaseRepository
from app.repositories.registry import RepositoryRegistry


class DrugInteractionRepository(BaseRepository[DrugInteractionORM]):
    def get_all(self) -> list[DrugInteractionORM]:
        statement = select(self.model)
        return list(self.db.execute(statement).scalars().all())


RepositoryRegistry.register(DrugInteractionORM, DrugInteractionRepository)
