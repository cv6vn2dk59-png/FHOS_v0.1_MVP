from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from app.ai_os.runtime import AIRuntime
from app.application.uow import UnitOfWork
from app.modules.clinical_reasoning.application.dynamic_consilium_service import DynamicConsiliumService
from app.modules.clinical_reasoning.application.knee_consilium_demo_service import (
    KneePainConsiliumDemoService,
)
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
from app.modules.clinical_reasoning.persistence.orm import (
    MultiAIConsiliumParticipantORM,
    MultiAIConsiliumRunORM,
)
from app.modules.clinical_reasoning.schemas.multi_ai_consilium import MultiAIConsiliumRequest


PROMPT_VERSION = "multi-ai-consilium.v1"
NORMALIZATION_SCHEMA_VERSION = "normalized-clinical-opinion.v1"
COMPARISON_ALGORITHM_VERSION = "multi-ai-comparison.v1"
CONSENSUS_ALGORITHM_VERSION = "multi-ai-consilium-consensus.v1"
CLINICAL_GRAPH_VERSION = "deterministic-fhos-knee.v1"
EXECUTION_MODE = "mock"
PROVIDER_EXECUTION_STATUS = "mock_only"
REAL_PROVIDER_CALLS = False


@dataclass(frozen=True)
class NormalizedClinicalOpinion:
    provider_code: str
    hypotheses: list[dict]
    leading_hypothesis_ids: list[str]
    safety_critical_hypothesis_ids: list[str]
    missing_evidence_ids: list[str]
    recommended_checks: list[str]
    prohibited_conclusions: list[str]
    limitations: list[str]
    confidence_statement: str
    is_mock: bool = True

    def as_dict(self) -> dict:
        return {
            "provider_code": self.provider_code,
            "hypotheses": self.hypotheses,
            "leading_hypothesis_ids": self.leading_hypothesis_ids,
            "safety_critical_hypothesis_ids": self.safety_critical_hypothesis_ids,
            "missing_evidence_ids": self.missing_evidence_ids,
            "recommended_checks": self.recommended_checks,
            "prohibited_conclusions": self.prohibited_conclusions,
            "limitations": self.limitations,
            "confidence_statement": self.confidence_statement,
            "is_mock": self.is_mock,
        }


class MultiAIConsiliumService:
    def __init__(
        self,
        uow: UnitOfWork,
        runtime: AIRuntime | None = None,
        consilium_service: DynamicConsiliumService | None = None,
    ) -> None:
        self.uow = uow
        self.runtime = runtime or AIRuntime()
        self.consilium_service = consilium_service or DynamicConsiliumService()

    async def run(self, data: MultiAIConsiliumRequest) -> dict:
        run_id = f"multi-ai:{uuid4()}"
        case_package = self._build_case_package(data)
        clinical_graph = self._build_clinical_graph(data)

        round_one = await self._run_round(
            round_number=1,
            independent=True,
            provider_codes=data.provider_codes,
            case_package=case_package,
            clinical_graph=clinical_graph,
            forced_failures=set(data.forced_failure_provider_codes),
            forced_invalid_normalization=set(data.forced_invalid_normalization_provider_codes),
        )
        comparison = self._build_comparison(
            clinical_graph=clinical_graph,
            participant_results=round_one["responses"],
        )

        rounds = [round_one]
        latest_responses = round_one["responses"]
        if data.require_independent_round and self._successful_count(latest_responses) >= 2:
            round_two = await self._run_round(
                round_number=2,
                independent=False,
                provider_codes=[
                    response["provider_code"]
                    for response in latest_responses
                    if response["status"] == "completed"
                ],
                case_package=case_package,
                clinical_graph=clinical_graph,
                comparison=comparison,
                forced_failures=set(),
                forced_invalid_normalization=set(),
            )
            rounds.append(round_two)
            latest_responses = round_two["responses"]

        consensus = self._build_consensus(
            data=data,
            clinical_graph=clinical_graph,
            participant_results=latest_responses,
            comparison=comparison,
        )
        devil_review = self._build_devil_review(
            data=data,
            clinical_graph=clinical_graph,
            comparison=comparison,
            consensus=consensus,
            rounds=rounds,
        ) if data.require_devil_review else {
            "status": "skipped",
            "checks": {},
            "findings": [],
        }

        warnings = sorted({
            warning
            for round_payload in rounds
            for response in round_payload["responses"]
            for warning in response.get("warnings", [])
        })
        limitations = sorted({
            *clinical_graph["limitations"],
            *consensus["limitations"],
            "Mock provider normalization is explicitly marked with is_mock=true until real provider JSON outputs are enabled.",
        })
        violations = list(consensus["violations"])
        if devil_review.get("status") == "failed":
            violations.append("devil_review_failed")

        participants = [
            {
                "provider_code": response["provider_code"],
                "model": response["model"],
                "status": response["status"],
                "latency_ms": response["latency_ms"],
                "is_mock": response["is_mock"],
                "fallback_used": response["fallback_used"],
            }
            for response in round_one["responses"]
        ]

        payload = {
            "run_id": run_id,
            "case_id": data.case_id,
            "execution_mode": EXECUTION_MODE,
            "is_mock": True,
            "real_provider_calls": REAL_PROVIDER_CALLS,
            "orchestration_status": "completed",
            "provider_execution_status": PROVIDER_EXECUTION_STATUS,
            "participants": participants,
            "rounds": rounds,
            "clinical_graph": clinical_graph,
            "comparison": comparison,
            "devil_review": devil_review,
            "consensus": consensus,
            "warnings": warnings,
            "limitations": limitations,
            "violations": violations,
        }
        self._persist_run(
            run_id=run_id,
            data=data,
            case_package=case_package,
            payload=payload,
        )
        return payload

    @staticmethod
    def _is_knee_case_text(value: str) -> bool:
        lowered = value.lower()
        return "коліно" in lowered or "knee" in lowered

    def _build_case_package(self, data: MultiAIConsiliumRequest) -> dict:
        return {
            "case_id": data.case_id,
            "case_text": data.case_text,
            "clinical_context": data.clinical_context,
            "language": data.language,
            "existing_branch_ids": data.existing_branch_ids,
            "facts": data.facts,
            "missing_evidence_ids": data.missing_evidence_ids,
            "safety_constraints": data.safety_constraints,
            "timeout_seconds": data.timeout_seconds,
            "prompt_version": PROMPT_VERSION,
            "normalization_schema_version": NORMALIZATION_SCHEMA_VERSION,
            "execution_mode": EXECUTION_MODE,
            "real_provider_calls": REAL_PROVIDER_CALLS,
        }

    def _build_clinical_graph(self, data: MultiAIConsiliumRequest) -> dict:
        if self._is_knee_case_text(data.case_text):
            demo = KneePainConsiliumDemoService().build()
            return {
                "clinical_graph_source": "deterministic_fhos",
                "clinical_graph_version": CLINICAL_GRAPH_VERSION,
                "symptom": demo["symptom"],
                "branches": [self._serialize_branch(branch) for branch in demo["branches"]],
                "branch_ids": [branch.id for branch in demo["branches"]],
                "safety_critical_branch_ids": sorted(
                    branch.id for branch in demo["branches"] if branch.safety_critical
                ),
                "missing_evidence_ids": sorted({
                    item
                    for branch in demo["branches"]
                    for item in branch.missing_evidence_ids
                }),
                "prohibited_conclusions": [
                    "diagnosis_confirmed",
                    "consensus_is_diagnosis",
                    "safety_branch_silently_removed",
                ],
                "limitations": [
                    "Clinical graph remains the control frame; provider outputs do not replace it.",
                    "The knee example is a structured scenario, not a confirmed diagnosis.",
                ],
            }

        branches = data.clinical_context.get("branches", [])
        if branches:
            safety_ids = sorted(
                branch["id"] for branch in branches if branch.get("safety_critical")
            )
            missing_ids = sorted({
                item
                for branch in branches
                for item in branch.get("missing_evidence_ids", [])
            })
            return {
                "clinical_graph_source": "request_context",
                "clinical_graph_version": "request-context.v1",
                "symptom": data.case_text,
                "branches": branches,
                "branch_ids": [branch["id"] for branch in branches],
                "safety_critical_branch_ids": safety_ids,
                "missing_evidence_ids": missing_ids,
                "prohibited_conclusions": [
                    "diagnosis_confirmed",
                    "consensus_is_diagnosis",
                ],
                "limitations": [
                    "Custom clinical graph was supplied by request context.",
                ],
            }

        raise ValueError(
            "Unable to build clinical graph. Provide a supported case text or clinical_context.branches."
        )

    async def _run_round(
        self,
        *,
        round_number: int,
        independent: bool,
        provider_codes: list[str],
        case_package: dict,
        clinical_graph: dict,
        forced_failures: set[str],
        forced_invalid_normalization: set[str],
        comparison: dict | None = None,
    ) -> dict:
        round_input = {
            "case_package": case_package,
            "clinical_graph": clinical_graph,
            "comparison": comparison,
            "round": round_number,
            "independent": independent,
        }
        input_hash = self._hash_payload(round_input)
        serialized_input = json.dumps(round_input, ensure_ascii=False, sort_keys=True)

        responses: list[dict] = []
        for provider_code in provider_codes:
            started_at = datetime.now(timezone.utc)
            if provider_code in forced_failures:
                completed_at = datetime.now(timezone.utc)
                responses.append({
                    "provider_code": provider_code,
                    "model": "placeholder",
                    "round": round_number,
                    "independent": independent,
                    "prompt_version": PROMPT_VERSION,
                    "input_hash": input_hash,
                    "raw_response": None,
                    "normalized_response": None,
                    "started_at": started_at.isoformat(),
                    "completed_at": completed_at.isoformat(),
                    "latency_ms": self._latency_ms(started_at, completed_at),
                    "is_mock": True,
                    "status": "failed",
                    "error": "forced_failure_for_test",
                    "fallback_used": False,
                    "warnings": [],
                })
                continue

            raw_response = await self.runtime.execute(
                provider=provider_code,
                system_prompt=self._system_prompt(),
                user_prompt=serialized_input,
                temperature=0.2,
            )
            completed_at = datetime.now(timezone.utc)
            response = {
                "provider_code": provider_code,
                "model": raw_response.get("model", "placeholder"),
                "round": round_number,
                "independent": independent,
                "prompt_version": PROMPT_VERSION,
                "input_hash": input_hash,
                "raw_response": raw_response,
                "normalized_response": None,
                "started_at": started_at.isoformat(),
                "completed_at": completed_at.isoformat(),
                "latency_ms": self._latency_ms(started_at, completed_at),
                "is_mock": True,
                "status": "completed",
                "error": None,
                "fallback_used": False,
                "warnings": [],
            }
            if provider_code in forced_invalid_normalization:
                response["status"] = "normalization_failed"
                response["error"] = "mock_normalization_failed"
                response["warnings"].append(
                    f"normalization_failed:{provider_code}:repair_attempt_exhausted"
                )
            else:
                normalized = self._mock_normalized_opinion(
                    provider_code=provider_code,
                    clinical_graph=clinical_graph,
                    round_number=round_number,
                )
                response["normalized_response"] = normalized.as_dict()
            responses.append(response)

        return {
            "round": round_number,
            "independent": independent,
            "input_hash": input_hash,
            "responses": responses,
        }

    def _mock_normalized_opinion(
        self,
        *,
        provider_code: str,
        clinical_graph: dict,
        round_number: int,
    ) -> NormalizedClinicalOpinion:
        if clinical_graph["clinical_graph_source"] != "deterministic_fhos":
            raise ValueError("Mock opinions are only configured for the deterministic FHOS knee graph.")
        return self._mock_knee_opinion(provider_code, clinical_graph, round_number)

    def _mock_knee_opinion(
        self,
        provider_code: str,
        clinical_graph: dict,
        round_number: int,
    ) -> NormalizedClinicalOpinion:
        branch_index = {branch["causal_domain"]: branch for branch in clinical_graph["branches"]}
        provider_candidate = self._provider_candidate_branch(
            provider_code="gemini",
            case_id="KNEE-DEMO-001",
            branch_id="acute_neurovascular_red_flag",
            title="Acute neurovascular red flag candidate",
            description="Provider-raised safety branch that requires FHOS validation before it can influence control-graph closure.",
        )

        round_one = {
            "openai": NormalizedClinicalOpinion(
                provider_code="openai",
                hypotheses=[
                    branch_index["mechanical_internal"],
                    branch_index["degenerative"],
                    branch_index["inflammatory"],
                ],
                leading_hypothesis_ids=[branch_index["mechanical_internal"]["id"]],
                safety_critical_hypothesis_ids=[branch_index["inflammatory"]["id"]],
                missing_evidence_ids=[
                    "missing:joint_line_exam",
                    "missing:mcmurray_or_thessaly",
                    "missing:crp_esr",
                ],
                recommended_checks=[
                    "targeted knee mechanical examination",
                    "plain knee radiography in context",
                    "inflammatory laboratory context",
                ],
                prohibited_conclusions=[
                    "diagnosis_confirmed",
                    "single_cause_confirmed",
                ],
                limitations=[
                    "Mechanical plausibility does not exclude inflammatory alternatives.",
                ],
                confidence_statement="Mechanical internal branch is leading, but this is not a confirmed diagnosis.",
            ),
            "claude": NormalizedClinicalOpinion(
                provider_code="claude",
                hypotheses=[
                    branch_index["mechanical_internal"],
                    branch_index["inflammatory"],
                    branch_index["vascular"],
                ],
                leading_hypothesis_ids=[branch_index["mechanical_internal"]["id"]],
                safety_critical_hypothesis_ids=[
                    branch_index["inflammatory"]["id"],
                    branch_index["vascular"]["id"],
                ],
                missing_evidence_ids=[
                    "missing:systemic_review",
                    "missing:duplex_ultrasound",
                ],
                recommended_checks=[
                    "vascular pulse and perfusion check",
                    "urgent duplex if vascular concern persists",
                    "systemic inflammatory review",
                ],
                prohibited_conclusions=[
                    "consensus_is_diagnosis",
                ],
                limitations=[
                    "Safety-critical alternatives remain unresolved without targeted exclusion.",
                ],
                confidence_statement="The leading branch remains provisional because vascular and inflammatory risks are not closed.",
            ),
            "gemini": NormalizedClinicalOpinion(
                provider_code="gemini",
                hypotheses=[
                    branch_index["mechanical_internal"],
                    branch_index["referred_pain"],
                    branch_index["infectious"],
                    provider_candidate,
                ],
                leading_hypothesis_ids=[branch_index["mechanical_internal"]["id"]],
                safety_critical_hypothesis_ids=[
                    branch_index["infectious"]["id"],
                    provider_candidate["id"],
                ],
                missing_evidence_ids=[
                    "missing:lumbar_screen",
                    "missing:aspiration",
                    "missing:neurovascular_repeat_exam",
                ],
                recommended_checks=[
                    "hip and lumbar screening",
                    "joint aspiration if septic concern persists",
                    "repeat neurovascular examination because a provider-specific safety concern was raised",
                ],
                prohibited_conclusions=[
                    "treatment_confirmed",
                ],
                limitations=[
                    "Referred pain and septic alternatives cannot be dismissed from symptom location alone.",
                    "The added provider candidate branch remains proposed until FHOS validation.",
                ],
                confidence_statement="A mechanical branch leads, but referred, infectious, and provider-proposed safety alternatives stay active.",
            ),
        }
        if round_number == 1:
            return round_one[provider_code]

        round_two = {
            "openai": NormalizedClinicalOpinion(
                provider_code="openai",
                hypotheses=[
                    branch_index["mechanical_internal"],
                    branch_index["degenerative"],
                    branch_index["inflammatory"],
                    branch_index["vascular"],
                ],
                leading_hypothesis_ids=[branch_index["mechanical_internal"]["id"]],
                safety_critical_hypothesis_ids=[
                    branch_index["inflammatory"]["id"],
                    branch_index["vascular"]["id"],
                ],
                missing_evidence_ids=sorted({
                    *round_one["openai"].missing_evidence_ids,
                    "missing:duplex_ultrasound",
                }),
                recommended_checks=round_one["openai"].recommended_checks + [
                    "vascular screening because another provider retained a vascular safety branch",
                ],
                prohibited_conclusions=round_one["openai"].prohibited_conclusions,
                limitations=[
                    "Round 2 incorporated cross-provider safety concerns without mutating round 1.",
                ],
                confidence_statement="Mechanical internal branch still leads, but vascular safety review must stay open.",
            ),
            "claude": NormalizedClinicalOpinion(
                provider_code="claude",
                hypotheses=[
                    branch_index["mechanical_internal"],
                    branch_index["inflammatory"],
                    branch_index["vascular"],
                    branch_index["infectious"],
                ],
                leading_hypothesis_ids=[branch_index["mechanical_internal"]["id"]],
                safety_critical_hypothesis_ids=[
                    branch_index["inflammatory"]["id"],
                    branch_index["vascular"]["id"],
                    branch_index["infectious"]["id"],
                ],
                missing_evidence_ids=sorted({
                    *round_one["claude"].missing_evidence_ids,
                    "missing:aspiration",
                }),
                recommended_checks=round_one["claude"].recommended_checks + [
                    "exclude septic joint if hot swollen knee or fever persists",
                ],
                prohibited_conclusions=round_one["claude"].prohibited_conclusions,
                limitations=[
                    "Round 2 expands safety branch coverage but still does not confirm diagnosis.",
                ],
                confidence_statement="Consensus can only be partial while multiple safety-critical branches remain unresolved.",
            ),
            "gemini": NormalizedClinicalOpinion(
                provider_code="gemini",
                hypotheses=[
                    branch_index["mechanical_internal"],
                    branch_index["referred_pain"],
                    branch_index["infectious"],
                    branch_index["inflammatory"],
                    provider_candidate,
                ],
                leading_hypothesis_ids=[branch_index["mechanical_internal"]["id"]],
                safety_critical_hypothesis_ids=[
                    branch_index["infectious"]["id"],
                    branch_index["inflammatory"]["id"],
                    provider_candidate["id"],
                ],
                missing_evidence_ids=sorted({
                    *round_one["gemini"].missing_evidence_ids,
                    "missing:crp_esr",
                }),
                recommended_checks=round_one["gemini"].recommended_checks + [
                    "preserve inflammatory screening because another provider retained that branch",
                ],
                prohibited_conclusions=round_one["gemini"].prohibited_conclusions,
                limitations=[
                    "Cross-provider comparison increases branch coverage but does not resolve causality.",
                ],
                confidence_statement="The leading branch is unchanged, but inflammatory, infectious, and provider-proposed safety alternatives remain open.",
            ),
        }
        return round_two[provider_code]

    def _build_comparison(
        self,
        *,
        clinical_graph: dict,
        participant_results: list[dict],
    ) -> dict:
        successful = [
            result for result in participant_results
            if result["status"] == "completed" and result["normalized_response"] is not None
        ]
        provider_hypotheses: dict[str, set[str]] = {}
        provider_leading: dict[str, set[str]] = {}
        provider_safety: dict[str, set[str]] = {}
        provider_missing: dict[str, set[str]] = {}
        provider_checks: dict[str, set[str]] = {}
        provider_prohibited: dict[str, set[str]] = {}
        hypothesis_snapshots: dict[str, dict] = {}

        for result in successful:
            normalized = result["normalized_response"]
            provider = result["provider_code"]
            provider_hypotheses[provider] = {
                item["id"] for item in normalized["hypotheses"]
            }
            provider_leading[provider] = set(normalized["leading_hypothesis_ids"])
            provider_safety[provider] = set(normalized["safety_critical_hypothesis_ids"])
            provider_missing[provider] = set(normalized["missing_evidence_ids"])
            provider_checks[provider] = set(normalized["recommended_checks"])
            provider_prohibited[provider] = set(normalized["prohibited_conclusions"])
            for hypothesis in normalized["hypotheses"]:
                hypothesis_snapshots[hypothesis["id"]] = hypothesis

        agreements = {
            "hypothesis_ids": self._intersection(provider_hypotheses),
            "leading_hypothesis_ids": self._intersection(provider_leading),
            "safety_critical_hypothesis_ids": self._intersection(provider_safety),
            "missing_evidence_ids": self._intersection(provider_missing),
            "recommended_checks": self._intersection(provider_checks),
            "prohibited_conclusions": self._intersection(provider_prohibited),
        }

        graph_safety = set(clinical_graph["safety_critical_branch_ids"])
        mentioned_hypotheses = set().union(*provider_hypotheses.values()) if provider_hypotheses else set()
        missed_safety = sorted(graph_safety - mentioned_hypotheses)

        branch_to_providers: dict[str, list[str]] = {}
        for provider, branch_ids in provider_hypotheses.items():
            for branch_id in branch_ids:
                branch_to_providers.setdefault(branch_id, []).append(provider)

        unique_hypotheses = []
        for branch_id, providers in sorted(branch_to_providers.items()):
            if len(providers) != 1:
                continue
            snapshot = hypothesis_snapshots[branch_id]
            unique_hypotheses.append({
                "branch_id": branch_id,
                "providers": providers,
                "status": snapshot.get("status", "active"),
                "source": snapshot.get("source", "clinical_graph"),
                "requires_validation": snapshot.get("requires_validation", False),
                "safety_critical": snapshot.get("safety_critical", False),
            })

        minority_opinions = [
            {
                "provider_code": item["providers"][0],
                "branch_id": item["branch_id"],
                "reason": "unique_hypothesis_branch",
            }
            for item in unique_hypotheses
        ]
        disagreements = {
            "leading_hypothesis_ids": {
                provider: sorted(values)
                for provider, values in provider_leading.items()
            },
            "safety_critical_hypothesis_ids": {
                provider: sorted(values)
                for provider, values in provider_safety.items()
            },
            "missing_evidence_ids": {
                provider: sorted(values)
                for provider, values in provider_missing.items()
            },
        }
        contradictions = [
            {
                "provider_code": result["provider_code"],
                "prohibited_conclusion": item,
            }
            for result in successful
            for item in result["normalized_response"]["prohibited_conclusions"]
            if item in {"diagnosis_confirmed", "treatment_confirmed", "consensus_is_diagnosis"}
        ]
        provider_failures = [
            {
                "provider_code": result["provider_code"],
                "status": result["status"],
                "error": result["error"],
            }
            for result in participant_results
            if result["status"] != "completed"
        ]
        return {
            "agreements": agreements,
            "disagreements": disagreements,
            "unique_hypotheses": unique_hypotheses,
            "missed_safety_branches": missed_safety,
            "contradictions": contradictions,
            "minority_opinions": minority_opinions,
            "provider_failures": provider_failures,
            "comparison_algorithm_version": COMPARISON_ALGORITHM_VERSION,
        }

    def _build_consensus(
        self,
        *,
        data: MultiAIConsiliumRequest,
        clinical_graph: dict,
        participant_results: list[dict],
        comparison: dict,
    ) -> dict:
        successful = [
            result for result in participant_results
            if result["status"] == "completed" and result["normalized_response"] is not None
        ]
        if self._is_insufficient_participants(data, participant_results):
            consensus_status = "insufficient_participants"
        elif not comparison["agreements"]["leading_hypothesis_ids"]:
            consensus_status = "no_consensus"
        elif (
            comparison["provider_failures"]
            or comparison["missed_safety_branches"]
            or comparison["unique_hypotheses"]
        ):
            consensus_status = "partial_consensus"
        else:
            consensus_status = "consensus"

        branch_lookup = {
            branch["id"]: self._branch_from_snapshot(data.case_id, branch)
            for branch in clinical_graph["branches"]
        }
        roles = [
            ConsiliumRole(
                code=result["provider_code"],
                title=f"Provider reviewer ({result['provider_code']})",
                focus_domains=[],
            )
            for result in successful
        ]
        reviews: list[BranchReview] = []
        proposed_provider_branches: list[dict] = []
        seen_proposed_ids: set[str] = set()

        for result in successful:
            normalized = result["normalized_response"]
            hypothesis_ids = {item["id"] for item in normalized["hypotheses"]}
            safety_ids = set(normalized["safety_critical_hypothesis_ids"])
            missing_ids = set(normalized["missing_evidence_ids"])
            for hypothesis in normalized["hypotheses"]:
                branch_id = hypothesis["id"]
                branch = branch_lookup.get(branch_id)
                if branch is None:
                    if branch_id not in seen_proposed_ids:
                        proposed_provider_branches.append({
                            **hypothesis,
                            "provider_code": result["provider_code"],
                        })
                        seen_proposed_ids.add(branch_id)
                    continue
                requested = sorted(set(branch.missing_evidence_ids) & missing_ids)
                position = (
                    ReviewPosition.SAFETY_HOLD
                    if branch_id in safety_ids or branch.safety_critical
                    else ReviewPosition.SUPPORTS
                )
                reviews.append(
                    BranchReview(
                        role_code=result["provider_code"],
                        branch_id=branch_id,
                        position=position,
                        rationale=f"{result['provider_code']} normalized round {result['round']} opinion",
                        requested_evidence_ids=requested,
                        confidence=0.65,
                        provenance=[
                            ProvenanceReference(
                                source_id=f"multi_ai:{result['provider_code']}",
                                source_version=NORMALIZATION_SCHEMA_VERSION,
                                locator=f"round:{result['round']}",
                            )
                        ],
                    )
                )

        dynamic = self.consilium_service.evaluate(
            data.case_id,
            list(branch_lookup.values()),
            roles,
            reviews,
            [],
        )
        summary = dynamic.consensus.summary
        if consensus_status == "insufficient_participants":
            summary = "Mock multi-AI orchestration did not reach the minimum participant threshold."
        elif consensus_status == "partial_consensus":
            summary = "Mock multi-AI orchestration reached partial consensus: the leading branch converges, while safety and minority differences remain visible."
        elif consensus_status == "no_consensus":
            summary = "Mock multi-AI orchestration found no consensus on a leading branch; alternatives remain visible."

        return {
            "retained_branch_ids": dynamic.consensus.retained_branch_ids,
            "leading_branch_ids": dynamic.consensus.leading_branch_ids,
            "unresolved_branch_ids": dynamic.consensus.unresolved_branch_ids,
            "unsafe_to_close_branch_ids": dynamic.consensus.unsafe_to_close_branch_ids,
            "minority_opinions": [
                {
                    "provider_code": item.role_code,
                    "branch_id": item.branch_id,
                    "position": item.position.value,
                    "rationale": item.rationale,
                }
                for item in dynamic.consensus.minority_opinions
            ] + comparison["minority_opinions"],
            "missing_evidence_ids": dynamic.consensus.missing_evidence_ids,
            "prohibited_conclusions": dynamic.consensus.prohibited_conclusions,
            "summary": summary,
            "consensus_status": consensus_status,
            "proposed_provider_branches": proposed_provider_branches,
            "limitations": dynamic.limitations,
            "violations": [violation.code for violation in dynamic.violations],
        }

    def _build_devil_review(
        self,
        *,
        data: MultiAIConsiliumRequest,
        clinical_graph: dict,
        comparison: dict,
        consensus: dict,
        rounds: list[dict],
    ) -> dict:
        round_one = rounds[0]
        round_one_providers = [item["provider_code"] for item in round_one["responses"]]
        missing_provider_codes = sorted(set(data.provider_codes) - set(round_one_providers))
        fallback_providers = [
            item["provider_code"]
            for item in round_one["responses"]
            if item["fallback_used"]
        ]
        unique_provider_safety = [
            item for item in comparison["unique_hypotheses"]
            if item["safety_critical"]
        ]
        normalization_failed = [
            item for round_payload in rounds for item in round_payload["responses"]
            if item["status"] == "normalization_failed"
        ]
        checks = {
            "all_claimed_providers_recorded": not missing_provider_codes,
            "no_hidden_fallback": not fallback_providers,
            "mock_mode_honestly_labeled": EXECUTION_MODE == "mock" and not REAL_PROVIDER_CALLS,
            "real_provider_calls_disabled": REAL_PROVIDER_CALLS is False,
            "round_one_input_hash_consistent": len({
                item["input_hash"] for item in round_one["responses"]
            }) == 1,
            "round_one_is_independent": round_one["independent"] is True and all(
                item["independent"] is True for item in round_one["responses"]
            ),
            "round_one_responses_preserved": all(
                item["round"] == 1 for item in round_one["responses"]
            ),
        }

        findings: list[dict] = []
        if comparison["missed_safety_branches"]:
            findings.append({
                "risk": "missed_safety_branch",
                "condition": "A safety-critical branch from the FHOS graph was not retained by provider outputs.",
                "required_check": "Preserve or re-open the missing safety branch in the final review.",
                "affected_branch_ids": comparison["missed_safety_branches"],
                "severity": "high",
                "provider_codes": [],
            })
        for item in unique_provider_safety:
            findings.append({
                "risk": "unique_provider_safety_branch",
                "condition": "A provider introduced a unique safety-critical branch that cannot be silently dropped.",
                "required_check": "Keep the branch visible as provider-proposed until FHOS validation is complete.",
                "affected_branch_ids": [item["branch_id"]],
                "severity": "high",
                "provider_codes": item["providers"],
            })
        if self._successful_count(round_one["responses"]) < 2:
            findings.append({
                "risk": "single_participant_not_multi_ai",
                "condition": "Only one provider produced a usable primary response.",
                "required_check": "Do not label the result as multi-AI consensus without at least two successful participants.",
                "affected_branch_ids": [],
                "severity": "high",
                "provider_codes": [
                    item["provider_code"]
                    for item in round_one["responses"]
                    if item["status"] == "completed" and item["normalized_response"] is not None
                ],
            })
        for contradiction in comparison["contradictions"]:
            findings.append({
                "risk": "forbidden_conclusion_detected",
                "condition": f"{contradiction['provider_code']} produced a prohibited clinical conclusion.",
                "required_check": "Keep the prohibited conclusion visible and exclude it from consensus.",
                "affected_branch_ids": [],
                "severity": "high",
                "provider_codes": [contradiction["provider_code"]],
            })
        for result in normalization_failed:
            findings.append({
                "risk": "normalization_failed",
                "condition": f"{result['provider_code']} returned an unusable structured response.",
                "required_check": "Keep raw response, exclude from consensus, and surface warning.",
                "affected_branch_ids": [],
                "severity": "medium",
                "provider_codes": [result["provider_code"]],
            })
        if missing_provider_codes:
            findings.append({
                "risk": "provider_response_missing",
                "condition": "One or more requested providers are missing from round 1 records.",
                "required_check": "Record every requested provider explicitly, including failed ones.",
                "affected_branch_ids": [],
                "severity": "high",
                "provider_codes": missing_provider_codes,
            })
        if fallback_providers:
            findings.append({
                "risk": "hidden_fallback_detected",
                "condition": "A provider response was marked as fallback-generated.",
                "required_check": "Expose fallback behavior explicitly or disable it for this workflow.",
                "affected_branch_ids": [],
                "severity": "high",
                "provider_codes": fallback_providers,
            })

        passed = all(checks.values()) and not findings and consensus["consensus_status"] != "insufficient_participants"
        return {
            "status": "passed" if passed else "failed",
            "checks": checks,
            "findings": findings,
        }

    def _persist_run(
        self,
        *,
        run_id: str,
        data: MultiAIConsiliumRequest,
        case_package: dict,
        payload: dict,
    ) -> None:
        round_one = payload["rounds"][0]
        run = self.uow.repo(MultiAIConsiliumRunORM).add(
            MultiAIConsiliumRunORM(
                run_id=run_id,
                case_id=data.case_id,
                mode=data.mode,
                execution_mode=payload["execution_mode"],
                requested_provider_codes=data.provider_codes,
                successful_provider_codes=[
                    participant["provider_code"]
                    for participant in payload["participants"]
                    if participant["status"] == "completed"
                ],
                failed_provider_codes=[
                    participant["provider_code"]
                    for participant in payload["participants"]
                    if participant["status"] != "completed"
                ],
                case_package=case_package,
                clinical_graph_snapshot=payload["clinical_graph"],
                comparison_snapshot=payload["comparison"],
                devil_review_snapshot=payload["devil_review"],
                consensus_snapshot=payload["consensus"],
                warnings=payload["warnings"],
                limitations=payload["limitations"],
                violations=payload["violations"],
                clinical_graph_version=payload["clinical_graph"]["clinical_graph_version"],
                prompt_version=PROMPT_VERSION,
                normalization_schema_version=NORMALIZATION_SCHEMA_VERSION,
                comparison_algorithm_version=COMPARISON_ALGORITHM_VERSION,
                consensus_algorithm_version=CONSENSUS_ALGORITHM_VERSION,
                round_one_input_hash=round_one["input_hash"],
            )
        )
        self.uow.session.flush()

        for round_payload in payload["rounds"]:
            for response in round_payload["responses"]:
                self.uow.repo(MultiAIConsiliumParticipantORM).add(
                    MultiAIConsiliumParticipantORM(
                        run_id=run.id,
                        provider_code=response["provider_code"],
                        round_number=round_payload["round"],
                        independent=response["independent"],
                        prompt_version=response["prompt_version"],
                        input_hash=response["input_hash"],
                        model=response["model"],
                        status=response["status"],
                        started_at=self._parse_datetime(response["started_at"]),
                        completed_at=self._parse_datetime(response["completed_at"]),
                        latency_ms=response["latency_ms"],
                        raw_response=response["raw_response"],
                        normalized_response=response["normalized_response"],
                        error=response["error"],
                        fallback_used=response["fallback_used"],
                        is_mock=response["is_mock"],
                    )
                )
        self.uow.commit()

    @staticmethod
    def _system_prompt() -> str:
        return (
            "This is not a final diagnosis. Do not hide alternative branches. "
            "Do not close safety-critical branches without sufficient data. "
            "Do not invent sources. Do not treat consensus as proof of causality. "
            "Return a structured response."
        )

    @staticmethod
    def _serialize_branch(branch: HypothesisBranch) -> dict:
        return {
            "id": branch.id,
            "title": branch.title,
            "description": branch.description,
            "causal_domain": branch.causal_domain,
            "branch_type": branch.branch_type,
            "supporting_fact_ids": branch.supporting_fact_ids,
            "contradicting_fact_ids": branch.contradicting_fact_ids,
            "missing_evidence_ids": branch.missing_evidence_ids,
            "evidence_strength": branch.evidence_strength,
            "confidence": branch.confidence,
            "status": branch.status.value,
            "safety_critical": branch.safety_critical,
            "source": "clinical_graph",
            "requires_validation": False,
        }

    @staticmethod
    def _provider_candidate_branch(
        *,
        provider_code: str,
        case_id: str,
        branch_id: str,
        title: str,
        description: str,
    ) -> dict:
        return {
            "id": f"{case_id}:provider:{provider_code}:{branch_id}",
            "title": title,
            "description": description,
            "causal_domain": branch_id,
            "branch_type": "provider_candidate",
            "supporting_fact_ids": ["fact:knee_pain"],
            "contradicting_fact_ids": [],
            "missing_evidence_ids": ["missing:neurovascular_repeat_exam"],
            "evidence_strength": "plausible",
            "confidence": 0.35,
            "status": "proposed",
            "safety_critical": True,
            "source": "provider",
            "requires_validation": True,
        }

    @staticmethod
    def _branch_from_snapshot(case_id: str, branch: dict) -> HypothesisBranch:
        missing = branch.get("missing_evidence_ids", [])
        supporting = branch.get("supporting_fact_ids", [])
        return HypothesisBranch(
            id=branch["id"],
            case_id=case_id,
            title=branch["title"],
            description=branch["description"],
            root_trigger_ids=supporting[:1] or ["fact:case"],
            causal_domain=branch["causal_domain"],
            branch_type=branch["branch_type"],
            node_ids=supporting + [f"mechanism:{branch['causal_domain']}"] + missing,
            edge_ids=[f"{branch['id']}:edge:{index}" for index, _ in enumerate(supporting or ["fact"], start=1)],
            supporting_fact_ids=supporting,
            contradicting_fact_ids=branch.get("contradicting_fact_ids", []),
            missing_evidence_ids=missing,
            evidence_strength=branch.get("evidence_strength", "plausible"),
            confidence=branch.get("confidence", 0.5),
            status=BranchStatus(branch.get("status", "active")),
            provenance=[
                ProvenanceReference(
                    source_id="multi_ai_graph_snapshot",
                    source_version="1",
                    locator=branch["id"],
                )
            ],
            safety_critical=branch.get("safety_critical", False),
        )

    @staticmethod
    def _intersection(mapping: dict[str, set[str]]) -> list[str]:
        if not mapping:
            return []
        values = list(mapping.values())
        return sorted(set.intersection(*values)) if values else []

    @staticmethod
    def _hash_payload(payload: dict) -> str:
        serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    @staticmethod
    def _latency_ms(started_at: datetime, completed_at: datetime) -> int:
        return int((completed_at - started_at).total_seconds() * 1000)

    @staticmethod
    def _successful_count(participant_results: list[dict]) -> int:
        return sum(
            1
            for result in participant_results
            if result["status"] == "completed" and result["normalized_response"] is not None
        )

    @staticmethod
    def _parse_datetime(value: str) -> datetime:
        return datetime.fromisoformat(value)

    def _is_insufficient_participants(
        self,
        data: MultiAIConsiliumRequest,
        participant_results: list[dict],
    ) -> bool:
        successful = self._successful_count(participant_results)
        if successful < 2:
            return True
        if data.mode == "strict" and successful < len(data.provider_codes):
            return True
        return successful < data.minimum_successful_providers
