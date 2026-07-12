from datetime import datetime, timezone

from sqlalchemy import select

from app.modules.clinical_reasoning.persistence.orm import ConsentEnvelopeORM, GuardianAuthorityORM, PatientNodeStateORM
from app.repositories.base import BaseRepository
from app.repositories.registry import RepositoryRegistry


class ConsentEnvelopeRepository(BaseRepository[ConsentEnvelopeORM]):
    def active_for(self, subject_patient_id: str, actor_id: str, purpose_code: str) -> list[ConsentEnvelopeORM]:
        now = datetime.now(timezone.utc)
        stmt = select(self.model).where(
            self.model.subject_patient_id == subject_patient_id,
            self.model.granted_to_actor_id == actor_id,
            self.model.purpose_code == purpose_code,
            self.model.status == "active",
            self.model.valid_from <= now,
            (self.model.expires_at.is_(None) | (self.model.expires_at > now)),
        )
        return list(self.db.execute(stmt).scalars().all())


class PatientNodeStateRepository(BaseRepository[PatientNodeStateORM]):
    def for_patients(self, patient_ids: list[str]) -> list[PatientNodeStateORM]:
        stmt = select(self.model).where(self.model.patient_id.in_(patient_ids))
        return list(self.db.execute(stmt).scalars().all())


class GuardianAuthorityRepository(BaseRepository[GuardianAuthorityORM]):
    def active_for(self, guardian_actor_id: str, child_patient_id: str):
        from datetime import date
        today = date.today()
        stmt = select(self.model).where(
            self.model.guardian_actor_id == guardian_actor_id,
            self.model.child_patient_id == child_patient_id,
            self.model.verification_status == "verified",
            self.model.valid_from <= today,
            (self.model.valid_until.is_(None) | (self.model.valid_until >= today)),
        )
        return list(self.db.execute(stmt).scalars().all())


RepositoryRegistry.register(ConsentEnvelopeORM, ConsentEnvelopeRepository)
RepositoryRegistry.register(PatientNodeStateORM, PatientNodeStateRepository)

RepositoryRegistry.register(GuardianAuthorityORM, GuardianAuthorityRepository)
