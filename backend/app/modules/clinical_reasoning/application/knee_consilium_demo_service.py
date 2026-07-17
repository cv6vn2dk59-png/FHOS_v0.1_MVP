from __future__ import annotations

from app.modules.clinical_reasoning.application.dynamic_consilium_service import DynamicConsiliumService
from app.modules.clinical_reasoning.domain.causality import ProvenanceReference
from app.modules.clinical_reasoning.domain.dynamic_consilium import (
    BranchReview,
    ConsiliumRole,
    ReviewPosition,
)
from app.modules.clinical_reasoning.domain.hypothesis_expansion import (
    BranchStatus,
    HypothesisBranch,
)


DEMO_PROVENANCE = [
    ProvenanceReference(
        source_id="FHOS_DEMO:KNEE_CONSILIUM",
        source_version="2026-07-17",
        locator="symptom:knee_pain",
    )
]


class KneePainConsiliumDemoService:
    def __init__(self, consilium_service: DynamicConsiliumService | None = None) -> None:
        self.consilium_service = consilium_service or DynamicConsiliumService()

    def build(self) -> dict:
        case_id = "KNEE-DEMO-001"
        symptom = "болить коліно"
        branches = self._branches(case_id)
        roles = self._roles()
        reviews = self._reviews(case_id)
        result = self.consilium_service.evaluate(case_id, branches, roles, reviews, [])
        return {
            "case_id": case_id,
            "symptom": symptom,
            "branches": branches,
            "roles": roles,
            "result": result,
        }

    def _branches(self, case_id: str) -> list[HypothesisBranch]:
        return [
            self._branch(
                case_id=case_id,
                branch_id="degenerative",
                title="Degenerative joint branch",
                description="Mechanical-degenerative joint explanation remains possible, but it is not a diagnosis.",
                causal_domain="degenerative",
                branch_type="alternative_mechanistic",
                supporting_fact_ids=["fact:knee_pain", "fact:load_related_pain", "fact:progressive_stiffness"],
                missing_evidence_ids=["missing:xray_context", "missing:crepitus_exam"],
                evidence_strength="plausible",
            ),
            self._branch(
                case_id=case_id,
                branch_id="inflammatory",
                title="Inflammatory joint branch",
                description="Inflammatory arthritis remains a separate branch and cannot be silently merged with degeneration.",
                causal_domain="inflammatory",
                branch_type="safety_alternative",
                supporting_fact_ids=["fact:knee_pain", "fact:morning_stiffness", "fact:effusion"],
                missing_evidence_ids=["missing:systemic_review", "missing:crp_esr"],
                evidence_strength="plausible",
                status=BranchStatus.UNSAFE_TO_CLOSE,
                safety_critical=True,
            ),
            self._branch(
                case_id=case_id,
                branch_id="mechanical_internal",
                title="Internal mechanical branch",
                description="Meniscus or ligament-related internal mechanical branch remains independent from other causes.",
                causal_domain="mechanical_internal",
                branch_type="primary_mechanistic",
                supporting_fact_ids=["fact:knee_pain", "fact:twisting_load", "fact:clicking_locking"],
                missing_evidence_ids=["missing:joint_line_exam", "missing:mcmurray_or_thessaly"],
                evidence_strength="supported",
            ),
            self._branch(
                case_id=case_id,
                branch_id="referred_pain",
                title="Referred pain branch",
                description="Hip or lumbar referral remains a separate branch even if the pain is felt in the knee.",
                causal_domain="referred_pain",
                branch_type="alternative_mechanistic",
                supporting_fact_ids=["fact:knee_pain", "fact:hip_or_back_context"],
                missing_evidence_ids=["missing:hip_exam", "missing:lumbar_screen"],
                evidence_strength="plausible",
            ),
            self._branch(
                case_id=case_id,
                branch_id="vascular",
                title="Vascular branch",
                description="A vascular explanation remains visible until urgent exclusion is complete.",
                causal_domain="vascular",
                branch_type="safety_alternative",
                supporting_fact_ids=["fact:knee_pain", "fact:calf_swelling", "fact:temperature_change"],
                missing_evidence_ids=["missing:pulse_exam", "missing:duplex_ultrasound"],
                evidence_strength="plausible",
                status=BranchStatus.UNSAFE_TO_CLOSE,
                safety_critical=True,
            ),
            self._branch(
                case_id=case_id,
                branch_id="infectious",
                title="Infectious branch",
                description="Septic joint branch remains visible as a safety-critical alternative.",
                causal_domain="infectious",
                branch_type="safety_alternative",
                supporting_fact_ids=["fact:knee_pain", "fact:hot_swollen_joint", "fact:fever"],
                missing_evidence_ids=["missing:aspiration", "missing:blood_culture"],
                evidence_strength="plausible",
                status=BranchStatus.UNSAFE_TO_CLOSE,
                safety_critical=True,
            ),
        ]

    def _roles(self) -> list[ConsiliumRole]:
        return [
            ConsiliumRole("orthopedics", "Orthopedics", ["degenerative", "mechanical_internal"]),
            ConsiliumRole("sports_medicine", "Sports Medicine", ["mechanical_internal"]),
            ConsiliumRole("rheumatology", "Rheumatology", ["inflammatory"]),
            ConsiliumRole("neurology", "Neurology", ["referred_pain"]),
            ConsiliumRole("vascular", "Vascular Surgery", ["vascular"]),
            ConsiliumRole("infectious_disease", "Infectious Disease", ["infectious"]),
            ConsiliumRole("devil", "Devil Review", devil_role=True),
        ]

    def _reviews(self, case_id: str) -> list[BranchReview]:
        return [
            self._review(
                "orthopedics",
                case_id,
                "degenerative",
                ReviewPosition.SUPPORTS,
                "Load-related pain and stiffness can fit a degenerative branch.",
            ),
            self._review(
                "devil",
                case_id,
                "degenerative",
                ReviewPosition.REQUESTS_EVIDENCE,
                "Degeneration should not outrank safety alternatives without imaging-context correlation.",
                requested=["missing:xray_context"],
            ),
            self._review(
                "rheumatology",
                case_id,
                "inflammatory",
                ReviewPosition.SUPPORTS,
                "Morning stiffness and effusion keep inflammatory arthritis active.",
            ),
            self._review(
                "devil",
                case_id,
                "inflammatory",
                ReviewPosition.SAFETY_HOLD,
                "Inflammatory branch stays unsafe to close until systemic review and inflammatory markers are checked.",
                requested=["missing:systemic_review", "missing:crp_esr"],
            ),
            self._review(
                "orthopedics",
                case_id,
                "mechanical_internal",
                ReviewPosition.SUPPORTS,
                "Twisting load with locking preserves an internal mechanical branch.",
            ),
            self._review(
                "sports_medicine",
                case_id,
                "mechanical_internal",
                ReviewPosition.SUPPORTS,
                "Mechanical provocation pattern supports a meniscal or ligament-related path.",
            ),
            self._review(
                "neurology",
                case_id,
                "referred_pain",
                ReviewPosition.SUPPORTS,
                "Hip or lumbar context keeps referred pain separate from local knee pathology.",
            ),
            self._review(
                "vascular",
                case_id,
                "vascular",
                ReviewPosition.SAFETY_HOLD,
                "Swelling and temperature change require urgent vascular exclusion.",
                requested=["missing:pulse_exam", "missing:duplex_ultrasound"],
            ),
            self._review(
                "infectious_disease",
                case_id,
                "infectious",
                ReviewPosition.SAFETY_HOLD,
                "A hot swollen joint with fever cannot be closed without aspiration or culture.",
                requested=["missing:aspiration", "missing:blood_culture"],
            ),
        ]

    @staticmethod
    def _branch(
        *,
        case_id: str,
        branch_id: str,
        title: str,
        description: str,
        causal_domain: str,
        branch_type: str,
        supporting_fact_ids: list[str],
        missing_evidence_ids: list[str],
        evidence_strength: str,
        status: BranchStatus = BranchStatus.ACTIVE,
        safety_critical: bool = False,
    ) -> HypothesisBranch:
        return HypothesisBranch(
            id=f"{case_id}:branch:{branch_id}",
            case_id=case_id,
            title=title,
            description=description,
            root_trigger_ids=["fact:knee_pain"],
            causal_domain=causal_domain,
            branch_type=branch_type,
            node_ids=supporting_fact_ids + [f"mechanism:{branch_id}"] + missing_evidence_ids,
            edge_ids=[f"{case_id}:edge:{branch_id}:{index}" for index, _ in enumerate(supporting_fact_ids, start=1)],
            supporting_fact_ids=supporting_fact_ids,
            missing_evidence_ids=missing_evidence_ids,
            evidence_strength=evidence_strength,
            confidence=0.65 if not safety_critical else 0.55,
            status=status,
            provenance=DEMO_PROVENANCE,
            safety_critical=safety_critical,
        )

    @staticmethod
    def _review(
        role_code: str,
        case_id: str,
        branch_id: str,
        position: ReviewPosition,
        rationale: str,
        *,
        requested: list[str] | None = None,
    ) -> BranchReview:
        return BranchReview(
            role_code=role_code,
            branch_id=f"{case_id}:branch:{branch_id}",
            position=position,
            rationale=rationale,
            requested_evidence_ids=requested or [],
            confidence=0.68,
            provenance=DEMO_PROVENANCE,
        )
