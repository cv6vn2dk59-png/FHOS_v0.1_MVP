from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import date, datetime, timezone


class ConsentStatus(str, enum.Enum):
    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"


class DisclosureLevel(str, enum.Enum):
    EXISTENCE_ONLY = "existence_only"
    CONCLUSION_ONLY = "conclusion_only"
    SELECTED_FACTS = "selected_facts"
    FULL_RESOURCE = "full_resource"


class AccessDecisionKind(str, enum.Enum):
    ALLOW = "allow"
    DENY = "deny"
    PARTIAL = "partial"


@dataclass
class ConsentEnvelope:
    subject_patient_id: str
    granted_to_actor_id: str
    purpose_code: str
    resource_node_ids: list[str]
    allowed_operations: list[str]
    disclosure_level: DisclosureLevel
    allow_derivation: bool = False
    allow_disclosure_of_derivation: bool = False
    valid_from: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime | None = None
    status: ConsentStatus = ConsentStatus.ACTIVE
    id: int | None = None
    revoked_at: datetime | None = None

    def is_active(self, at: datetime | None = None) -> bool:
        at = at or datetime.now(timezone.utc)
        return self.status == ConsentStatus.ACTIVE and self.valid_from <= at and (
            self.expires_at is None or at < self.expires_at
        )

    def revoke(self, at: datetime | None = None) -> None:
        if self.status == ConsentStatus.REVOKED:
            return
        self.status = ConsentStatus.REVOKED
        self.revoked_at = at or datetime.now(timezone.utc)


@dataclass
class GuardianAuthority:
    guardian_actor_id: str
    child_patient_id: str
    authority_type: str
    jurisdiction_code: str
    valid_from: date
    valid_until: date | None = None
    verification_status: str = "verified"
    restrictions: list[str] = field(default_factory=list)
    id: int | None = None


@dataclass
class JurisdictionPolicy:
    jurisdiction_code: str
    policy_type: str
    threshold_age: int | None
    effective_from: date
    source_uri: str
    source_version: str
    effective_to: date | None = None
    id: int | None = None


@dataclass
class CareTransitionEvent:
    patient_id: str
    policy_id: int
    expected_at: datetime
    status: str = "scheduled"
    id: int | None = None


@dataclass
class FamilyAccessDecision:
    decision: AccessDecisionKind
    reason_codes: list[str]
    permitted_node_ids: list[str] = field(default_factory=list)
    disclosure_level: DisclosureLevel | None = None
    consent_basis_ids: list[int] = field(default_factory=list)
