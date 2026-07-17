from datetime import datetime, timezone

from sqlalchemy import select

from app.modules.clinical_reasoning.persistence.orm import (
    ConsentEnvelopeORM,
    GuardianAuthorityORM,
    MultiAIConsiliumParticipantORM,
    MultiAIConsiliumRunORM,
    PatientNodeStateORM,
    RulePassportORM,
)
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


class RulePassportRepository(BaseRepository[RulePassportORM]):
    """FHOS-RULE-R-11: пошук паспорта клінічного правила за rule_id."""

    def by_rule_id(self, rule_id: str) -> list[RulePassportORM]:
        stmt = select(self.model).where(self.model.rule_id == rule_id).order_by(self.model.version.desc())
        return list(self.db.execute(stmt).scalars().all())

    def active_by_rule_id(self, rule_id: str) -> RulePassportORM | None:
        stmt = select(self.model).where(
            self.model.rule_id == rule_id,
            self.model.status == "active",
        )
        return self.db.execute(stmt).scalar_one_or_none()


RepositoryRegistry.register(RulePassportORM, RulePassportRepository)


class MultiAIConsiliumRunRepository(BaseRepository[MultiAIConsiliumRunORM]):
    def by_run_id(self, run_id: str) -> MultiAIConsiliumRunORM | None:
        stmt = select(self.model).where(self.model.run_id == run_id)
        return self.db.execute(stmt).scalar_one_or_none()


RepositoryRegistry.register(MultiAIConsiliumRunORM, MultiAIConsiliumRunRepository)
RepositoryRegistry.register(MultiAIConsiliumParticipantORM, BaseRepository)


class HealthNodeRepository(BaseRepository):
    def by_external_id(self, external_id: str):
        from app.modules.clinical_reasoning.persistence.orm import HealthNodeORM
        stmt = select(HealthNodeORM).where(HealthNodeORM.external_id == external_id)
        return self.db.execute(stmt).scalar_one_or_none()


class HealthRelationRepository(BaseRepository):
    def causes_for(self, symptom_node_id: str, limit: int = 25):
        from app.modules.clinical_reasoning.persistence.orm import HealthNodeORM, HealthRelationORM
        stmt = (
            select(HealthRelationORM, HealthNodeORM)
            .join(HealthNodeORM, HealthNodeORM.external_id == HealthRelationORM.to_node_id)
            .where(
                HealthRelationORM.from_node_id == symptom_node_id,
                HealthRelationORM.relation_kind == "can_explain",
            )
            .limit(limit)
        )
        return list(self.db.execute(stmt).all())


from app.modules.clinical_reasoning.persistence.orm import HealthNodeORM, HealthRelationORM
RepositoryRegistry.register(HealthNodeORM, HealthNodeRepository)
RepositoryRegistry.register(HealthRelationORM, HealthRelationRepository)


class LaboratoryGraphObservationRepository(BaseRepository):
    def by_laboratory_result_id(self, laboratory_result_id: int):
        from app.modules.clinical_reasoning.persistence.orm import LaboratoryGraphObservationORM
        stmt = select(LaboratoryGraphObservationORM).where(
            LaboratoryGraphObservationORM.laboratory_result_id == laboratory_result_id
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def for_episode(self, patient_id: str, episode_id: str):
        from app.modules.clinical_reasoning.persistence.orm import LaboratoryGraphObservationORM
        stmt = (
            select(LaboratoryGraphObservationORM)
            .where(
                LaboratoryGraphObservationORM.patient_id == patient_id,
                LaboratoryGraphObservationORM.episode_id == episode_id,
            )
            .order_by(LaboratoryGraphObservationORM.laboratory_result_id.asc())
        )
        return list(self.db.execute(stmt).scalars().all())


from app.modules.clinical_reasoning.persistence.orm import LaboratoryGraphObservationORM
RepositoryRegistry.register(LaboratoryGraphObservationORM, LaboratoryGraphObservationRepository)
