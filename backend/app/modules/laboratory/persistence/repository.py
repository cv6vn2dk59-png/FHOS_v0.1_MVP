from sqlalchemy import select

from app.modules.laboratory.persistence.orm import LaboratoryResultORM
from app.repositories.base import BaseRepository
from app.repositories.registry import RepositoryRegistry


class LaboratoryRepository(BaseRepository[LaboratoryResultORM]):
    def get_results_for_patient(
        self,
        patient_profile_id: int,
        test_code: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[LaboratoryResultORM]:
        statement = (
            select(self.model)
            .where(self.model.patient_profile_id == patient_profile_id)
            .order_by(self.model.result_date.asc())
            .offset(skip)
            .limit(limit)
        )
        if test_code is not None:
            statement = statement.where(self.model.test_code == test_code)

        return list(self.db.execute(statement).scalars().all())

    def get_latest_result(
        self,
        patient_profile_id: int,
        test_code: str,
    ) -> LaboratoryResultORM | None:
        statement = (
            select(self.model)
            .where(
                self.model.patient_profile_id == patient_profile_id,
                self.model.test_code == test_code,
            )
            .order_by(self.model.result_date.desc())
            .limit(1)
        )
        return self.db.execute(statement).scalar_one_or_none()


RepositoryRegistry.register(LaboratoryResultORM, LaboratoryRepository)