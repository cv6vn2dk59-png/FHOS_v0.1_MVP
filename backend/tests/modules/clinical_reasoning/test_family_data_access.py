from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.persistence.model_registry  # noqa: F401
from app.application.uow import UnitOfWork
from app.modules.clinical_reasoning.application.service import FamilyDataAccessService
from app.modules.clinical_reasoning.persistence.orm import HealthNodeORM, PatientNodeStateORM
from app.persistence.base import Base


def make_uow():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    return UnitOfWork(factory)


def seed_states(uow):
    uow.repo(HealthNodeORM).add(HealthNodeORM(external_id="MONDO:STAPH", external_source="MONDO", label="Staphylococcal infection", node_kind="Disease"))
    for patient in ("husband", "wife"):
        uow.repo(PatientNodeStateORM).add(PatientNodeStateORM(patient_id=patient, node_id="MONDO:STAPH", episode_id="episode-1", activated_at=datetime.now(timezone.utc), family_link_reason="shared_pathogen"))
    uow.commit()


def test_deny_by_default_then_allow_then_revoke():
    with make_uow() as uow:
        seed_states(uow)
        service = FamilyDataAccessService(uow)
        assert service.authorized_shared_nodes("husband", ["husband", "wife"], "shared_infection_assessment") == {}

        consent = service.create_consent(
            subject_patient_id="wife",
            granted_to_actor_id="husband",
            purpose_code="shared_infection_assessment",
            resource_node_ids=["MONDO:STAPH"],
            allowed_operations=["compare"],
            disclosure_level="conclusion_only",
            allow_derivation=True,
            allow_disclosure_of_derivation=True,
            valid_from=datetime.now(timezone.utc) - timedelta(minutes=1),
            expires_at=None,
        )
        assert service.authorized_shared_nodes("husband", ["husband", "wife"], "shared_infection_assessment") == {"MONDO:STAPH": ["husband", "wife"]}

        service.revoke_consent(consent.id)
        assert service.authorized_shared_nodes("husband", ["husband", "wife"], "shared_infection_assessment") == {}
        assert uow.repo(type(consent)).get(consent.id).status == "revoked"
        assert uow.repo(type(consent)).get(consent.id).revoked_at is not None


def test_verified_guardian_authority_allows_without_child_consent():
    from datetime import date
    from app.modules.clinical_reasoning.persistence.orm import GuardianAuthorityORM

    with make_uow() as uow:
        seed_states(uow)
        uow.repo(GuardianAuthorityORM).add(GuardianAuthorityORM(
            guardian_actor_id="parent",
            child_patient_id="wife",
            authority_type="parent",
            jurisdiction_code="UA",
            valid_from=date(2020, 1, 1),
            valid_until=None,
            verification_status="verified",
            restrictions=[],
        ))
        uow.commit()
        decision = FamilyDataAccessService(uow).decide(
            "parent", "wife", "care", "compare", ["MONDO:STAPH"]
        )
        assert decision.decision.value == "allow"
        assert "verified_guardian_authority" in decision.reason_codes
