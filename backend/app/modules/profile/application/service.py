from app.application.uow import UnitOfWork
from app.modules.profile.persistence.orm import PatientProfileORM
from app.modules.profile.schemas.profile import PatientProfileCreate


class ProfileService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def create_profile(self, data: PatientProfileCreate) -> PatientProfileORM:
        profile = PatientProfileORM(
            first_name=data.first_name,
            last_name=data.last_name,
            birth_date=data.birth_date,
            sex=data.sex,
            phone=data.phone,
            email=str(data.email) if data.email else None,
        )

        created = self.uow.repo(PatientProfileORM).add(profile)
        self.uow.commit()

        return created

    def list_profiles(self) -> list[PatientProfileORM]:
        return self.uow.repo(PatientProfileORM).list()