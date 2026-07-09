from sqlalchemy import select

from app.modules.contraindications.persistence.orm import ContraindicationORM
from app.repositories.base import BaseRepository
from app.repositories.registry import RepositoryRegistry


class ContraindicationRepository(BaseRepository[ContraindicationORM]):
    def get_all(self) -> list[ContraindicationORM]:
        statement = select(self.model)
        return list(self.db.execute(statement).scalars().all())


RepositoryRegistry.register(ContraindicationORM, ContraindicationRepository)
