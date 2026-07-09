from sqlalchemy import select

from app.modules.icd11.persistence.orm import ICD11NodeORM
from app.repositories.base import BaseRepository
from app.repositories.registry import RepositoryRegistry


class ICD11NodeRepository(BaseRepository[ICD11NodeORM]):
    def get_all(self) -> list[ICD11NodeORM]:
        statement = select(self.model).order_by(self.model.sort_order)
        return list(self.db.execute(statement).scalars().all())

    def get_children(self, parent_id: str | None) -> list[ICD11NodeORM]:
        statement = (
            select(self.model)
            .where(self.model.parent_id == parent_id)
            .order_by(self.model.sort_order)
        )
        return list(self.db.execute(statement).scalars().all())


RepositoryRegistry.register(ICD11NodeORM, ICD11NodeRepository)
