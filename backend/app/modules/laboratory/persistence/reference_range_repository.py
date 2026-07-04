from sqlalchemy import select

from app.modules.laboratory.persistence.reference_range_orm import ReferenceRangeORM
from app.repositories.base import BaseRepository
from app.repositories.registry import RepositoryRegistry


class ReferenceRangeRepository(BaseRepository[ReferenceRangeORM]):
    def get_candidates(self, test_code: str, unit: str) -> list[ReferenceRangeORM]:
        """Повертає всі активні діапазони для test_code+unit.

        Фінальний вибір найкращого кандидата (sex/age/laboratory/method
        специфічність) виконує Domain (ReferenceRange.matches() /
        specificity_score()) на рівні Resolver, не тут — щоб клінічне
        правило не дублювалось між SQL і Python.
        """
        statement = select(self.model).where(
            self.model.test_code == test_code,
            self.model.unit == unit,
            self.model.is_active.is_(True),
        )
        return list(self.db.execute(statement).scalars().all())


RepositoryRegistry.register(ReferenceRangeORM, ReferenceRangeRepository)