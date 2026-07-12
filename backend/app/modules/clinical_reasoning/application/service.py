from datetime import datetime, timezone

from app.application.uow import UnitOfWork
from app.modules.clinical_reasoning.domain.access import AccessDecisionKind, DisclosureLevel, FamilyAccessDecision
from app.modules.clinical_reasoning.persistence.orm import ConsentEnvelopeORM, GuardianAuthorityORM, PatientNodeStateORM


class AccessDeniedError(Exception):
    pass


class FamilyDataAccessService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def create_consent(self, **data) -> ConsentEnvelopeORM:
        obj = ConsentEnvelopeORM(**data)
        self.uow.repo(ConsentEnvelopeORM).add(obj)
        self.uow.commit()
        return obj

    def revoke_consent(self, consent_id: int) -> ConsentEnvelopeORM:
        obj = self.uow.repo(ConsentEnvelopeORM).get(consent_id)
        if obj is None:
            raise LookupError("ConsentEnvelope not found")
        obj.status = "revoked"
        obj.revoked_at = datetime.now(timezone.utc)
        self.uow.commit()
        return obj

    def decide(self, actor_id: str, subject_patient_id: str, purpose_code: str, operation: str, node_ids: list[str]) -> FamilyAccessDecision:
        if actor_id == subject_patient_id:
            return FamilyAccessDecision(AccessDecisionKind.ALLOW, ["self_access"], node_ids, DisclosureLevel.FULL_RESOURCE)

        guardians = self.uow.repo(GuardianAuthorityORM).active_for(actor_id, subject_patient_id)
        for authority in guardians:
            if operation not in authority.restrictions:
                return FamilyAccessDecision(
                    AccessDecisionKind.ALLOW,
                    ["verified_guardian_authority"],
                    node_ids,
                    DisclosureLevel.SELECTED_FACTS,
                )

        consents = self.uow.repo(ConsentEnvelopeORM).active_for(subject_patient_id, actor_id, purpose_code)
        permitted: set[str] = set()
        basis: list[int] = []
        disclosure: DisclosureLevel | None = None
        for consent in consents:
            if operation not in consent.allowed_operations:
                continue
            permitted.update(set(node_ids) & set(consent.resource_node_ids))
            basis.append(consent.id)
            disclosure = DisclosureLevel(consent.disclosure_level)

        if not permitted:
            return FamilyAccessDecision(AccessDecisionKind.DENY, ["no_active_scoped_consent"])
        kind = AccessDecisionKind.ALLOW if permitted == set(node_ids) else AccessDecisionKind.PARTIAL
        return FamilyAccessDecision(kind, ["active_scoped_consent"], sorted(permitted), disclosure, basis)

    def authorized_shared_nodes(self, actor_id: str, patient_ids: list[str], purpose_code: str) -> dict[str, list[str]]:
        states = self.uow.repo(PatientNodeStateORM).for_patients(patient_ids)
        by_node: dict[str, list[str]] = {}
        for state in states:
            decision = self.decide(actor_id, state.patient_id, purpose_code, "compare", [state.node_id])
            if decision.decision == AccessDecisionKind.DENY:
                continue
            by_node.setdefault(state.node_id, [])
            if state.patient_id not in by_node[state.node_id]:
                by_node[state.node_id].append(state.patient_id)
        return {node: members for node, members in by_node.items() if len(members) >= 2}
