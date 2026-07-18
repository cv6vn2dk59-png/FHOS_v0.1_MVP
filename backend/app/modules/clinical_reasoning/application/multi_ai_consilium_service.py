from __future__ import annotations

import asyncio
import hashlib
import json
from dataclasses import dataclass, field
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


SYSTEM_PROMPT_VERSION = "multi-ai-system.v1"
ROUND_ONE_PROMPT_VERSION = "multi-ai-round-one.v1"
ROUND_TWO_PROMPT_VERSION = "multi-ai-round-two.v1"
DEVIL_PROMPT_VERSION = "multi-ai-devil.v1"
NORMALIZATION_SCHEMA_VERSION = "normalized-clinical-opinion.v2"
COMPARISON_ALGORITHM_VERSION = "multi-ai-comparison.v2"
CONSENSUS_ALGORITHM_VERSION = "multi-ai-consilium-consensus.v2"
CLINICAL_GRAPH_VERSION = "deterministic-fhos-knee.v1"


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
    supported_branch_ids: list[str] = field(default_factory=list)
    challenged_branch_ids: list[str] = field(default_factory=list)
    proposed_branches: list[dict] = field(default_factory=list)
    minority_opinions: list[dict] = field(default_factory=list)

    def as_dict(self) -> dict:
        supported_branch_ids = self.supported_branch_ids or [item["id"] for item in self.hypotheses]
        return {
            "provider_code": self.provider_code,
            "hypotheses": self.hypotheses,
            "leading_hypothesis_ids": self.leading_hypothesis_ids,
            "supported_branch_ids": supported_branch_ids,
            "challenged_branch_ids": self.challenged_branch_ids,
            "proposed_branches": self.proposed_branches,
            "minority_opinions": self.minority_opinions,
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
        execution_mode = self._requested_execution_mode(data)
        consensus_mode = self._consensus_mode(data)
        self._validate_request(data, execution_mode)

        run_id = f"multi-ai:{uuid4()}"
        case_package = self._build_case_package(data, execution_mode)
        clinical_graph = self._build_clinical_graph(data)

        round_one = await self._run_round(
            round_number=1,
            independent=True,
            provider_codes=data.provider_codes,
            case_package=case_package,
            clinical_graph=clinical_graph,
            execution_mode=execution_mode,
            timeout_seconds=data.timeout_seconds,
            max_retries=data.max_retries,
            forced_failures=set(data.forced_failure_provider_codes),
            forced_invalid_normalization=set(data.forced_invalid_normalization_provider_codes),
        )
        comparison = self._build_comparison(
            clinical_graph=clinical_graph,
            participant_results=round_one["responses"],
        )

        rounds = [round_one]
        latest_responses = round_one["responses"]
        if self._require_round_two(data) and self._successful_count(latest_responses) >= 2:
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
                execution_mode=execution_mode,
                timeout_seconds=data.timeout_seconds,
                max_retries=data.max_retries,
                comparison=comparison,
                forced_failures=set(),
                forced_invalid_normalization=set(),
            )
            rounds.append(round_two)
            latest_responses = round_two["responses"]

        provider_execution_status = self._provider_execution_status(round_one["responses"])
        successful_providers = [
            item["provider_code"]
            for item in round_one["responses"]
            if item["status"] == "completed" and item["normalized_response"] is not None
        ]
        failed_providers = [
            item["provider_code"]
            for item in round_one["responses"]
            if item["status"] != "completed" or item["normalized_response"] is None
        ]

        consensus = self._build_consensus(
            clinical_graph=clinical_graph,
            participant_results=latest_responses,
            comparison=comparison,
            consensus_mode=consensus_mode,
            minimum_successful_providers=data.minimum_successful_providers,
            requested_provider_count=len(data.provider_codes),
        )
        devil_review = self._build_devil_review(
            requested_provider_codes=data.provider_codes,
            rounds=rounds,
            comparison=comparison,
            consensus=consensus,
            execution_mode=execution_mode,
            provider_execution_status=provider_execution_status,
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
        })
        violations = list(consensus["violations"])
        if devil_review.get("status") == "failed":
            violations.append("devil_review_failed")

        participants = [
            {
                "provider_code": response["provider_code"],
                "provider_model": response["provider_model"],
                "execution_mode": response["execution_mode"],
                "status": response["status"],
                "latency_ms": response["latency_ms"],
                "is_mock": response["is_mock"],
                "real_provider_call": response["real_provider_call"],
                "fallback_used": response["fallback_used"],
                "usage": response["usage"],
            }
            for response in round_one["responses"]
        ]

        payload = {
            "run_id": run_id,
            "case_id": data.case_id,
            "execution_mode": execution_mode,
            "is_mock": provider_execution_status != "real_only",
            "real_provider_calls": any(
                response["real_provider_call"]
                for round_payload in rounds
                for response in round_payload["responses"]
            ),
            "orchestration_status": "completed",
            "provider_execution_status": provider_execution_status,
            "requested_providers": list(data.provider_codes),
            "executed_providers": [response["provider_code"] for response in round_one["responses"]],
            "successful_providers": successful_providers,
            "failed_providers": failed_providers,
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
            case_package=case_package,
            payload=payload,
        )
        return payload

    @staticmethod
    def _requested_execution_mode(data: MultiAIConsiliumRequest) -> str:
        value = (data.execution_mode or "mock").strip().lower()
        if value not in {"mock", "real", "mixed"}:
            raise ValueError("execution_mode must be one of: mock, real, mixed")
        return value

    @staticmethod
    def _consensus_mode(data: MultiAIConsiliumRequest) -> str:
        value = data.mode or data.consensus_mode or "demo"
        return value.strip().lower()

    @staticmethod
    def _require_round_two(data: MultiAIConsiliumRequest) -> bool:
        if data.require_independent_round is not None:
            return data.require_independent_round
        return data.require_round_two

    @staticmethod
    def _is_knee_case_text(value: str) -> bool:
        lowered = value.lower()
        return "коліно" in lowered or "knee" in lowered

    def _validate_request(self, data: MultiAIConsiliumRequest, execution_mode: str) -> None:
        if any(provider.strip().lower() == "auto" for provider in data.provider_codes):
            raise ValueError("provider_codes must be explicit. 'auto' is not allowed for multi-AI runs.")
        if execution_mode == "real" and data.allow_fallback:
            raise ValueError("allow_fallback is not supported in real multi-AI runs yet.")

    def _build_case_package(self, data: MultiAIConsiliumRequest, execution_mode: str) -> dict:
        payload = {
            "case_id": data.case_id,
            "case_text": data.case_text,
            "clinical_context": data.clinical_context,
            "language": data.language,
            "existing_branch_ids": data.existing_branch_ids,
            "facts": data.facts,
            "missing_evidence_ids": data.missing_evidence_ids,
            "safety_constraints": data.safety_constraints,
            "timeout_seconds": data.timeout_seconds,
            "execution_mode": execution_mode,
            "system_prompt_version": SYSTEM_PROMPT_VERSION,
            "round_one_prompt_version": ROUND_ONE_PROMPT_VERSION,
            "round_two_prompt_version": ROUND_TWO_PROMPT_VERSION,
            "devil_prompt_version": DEVIL_PROMPT_VERSION,
            "normalization_schema_version": NORMALIZATION_SCHEMA_VERSION,
        }
        payload["case_package_hash"] = self._hash_payload(payload)
        return payload

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
        execution_mode: str,
        timeout_seconds: int,
        max_retries: int,
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
        system_prompt = self._system_prompt(round_number)
        user_prompt = json.dumps(round_input, ensure_ascii=False, sort_keys=True)
        prompt_hash = self._hash_text(system_prompt + "\n" + user_prompt)
        prompt_version = ROUND_ONE_PROMPT_VERSION if round_number == 1 else ROUND_TWO_PROMPT_VERSION

        tasks = [
            self._run_provider(
                provider_code=provider_code,
                round_number=round_number,
                independent=independent,
                case_package=case_package,
                clinical_graph=clinical_graph,
                requested_execution_mode=execution_mode,
                timeout_seconds=timeout_seconds,
                max_retries=max_retries,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                input_hash=input_hash,
                prompt_hash=prompt_hash,
                prompt_version=prompt_version,
                force_failure=provider_code in forced_failures,
                force_invalid_normalization=provider_code in forced_invalid_normalization,
            )
            for provider_code in provider_codes
        ]
        responses = await asyncio.gather(*tasks)
        return {
            "round": round_number,
            "independent": independent,
            "input_hash": input_hash,
            "prompt_hash": prompt_hash,
            "prompt_version": prompt_version,
            "responses": responses,
        }

    async def _run_provider(
        self,
        *,
        provider_code: str,
        round_number: int,
        independent: bool,
        case_package: dict,
        clinical_graph: dict,
        requested_execution_mode: str,
        timeout_seconds: int,
        max_retries: int,
        system_prompt: str,
        user_prompt: str,
        input_hash: str,
        prompt_hash: str,
        prompt_version: str,
        force_failure: bool,
        force_invalid_normalization: bool,
    ) -> dict:
        actual_execution_mode = self._resolve_provider_execution_mode(
            provider_code,
            requested_execution_mode,
        )
        if force_failure:
            now = datetime.now(timezone.utc).isoformat()
            return {
                "provider_code": provider_code,
                "provider_model": "placeholder",
                "execution_mode": actual_execution_mode,
                "round": round_number,
                "independent": independent,
                "prompt_version": prompt_version,
                "input_hash": input_hash,
                "prompt_hash": prompt_hash,
                "raw_response": None,
                "normalized_response": None,
                "started_at": now,
                "completed_at": now,
                "latency_ms": 0,
                "is_mock": actual_execution_mode != "real",
                "real_provider_call": False,
                "status": "failed",
                "error": "forced_failure_for_test",
                "error_code": "forced_failure_for_test",
                "error_message": "forced_failure_for_test",
                "fallback_used": False,
                "attempt_count": 0,
                "usage": None,
                "warnings": [],
            }

        runtime_result = await self.runtime.execute(
            provider=provider_code,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.2,
            execution_mode=actual_execution_mode,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
        )
        response = {
            "provider_code": provider_code,
            "provider_model": runtime_result.get("model", "placeholder"),
            "execution_mode": actual_execution_mode,
            "round": round_number,
            "independent": independent,
            "prompt_version": prompt_version,
            "input_hash": input_hash,
            "prompt_hash": prompt_hash,
            "raw_response": runtime_result.get("raw_response"),
            "normalized_response": None,
            "started_at": runtime_result.get("started_at"),
            "completed_at": runtime_result.get("completed_at"),
            "latency_ms": runtime_result.get("latency_ms", 0),
            "is_mock": runtime_result.get("is_mock", actual_execution_mode != "real"),
            "real_provider_call": runtime_result.get("real_provider_call", False),
            "status": runtime_result.get("status", "failed"),
            "error": runtime_result.get("error_message"),
            "error_code": runtime_result.get("error_code"),
            "error_message": runtime_result.get("error_message"),
            "fallback_used": runtime_result.get("fallback_used", False),
            "attempt_count": runtime_result.get("attempt_count", 0),
            "usage": runtime_result.get("usage"),
            "warnings": [],
        }
        if response["status"] != "completed":
            return response

        if force_invalid_normalization:
            response["status"] = "normalization_failed"
            response["error"] = "mock_normalization_failed"
            response["error_code"] = "mock_normalization_failed"
            response["error_message"] = "mock_normalization_failed"
            response["warnings"].append(
                f"normalization_failed:{provider_code}:repair_attempt_exhausted"
            )
            return response

        try:
            if response["is_mock"]:
                normalized = self._mock_normalized_opinion(
                    provider_code=provider_code,
                    clinical_graph=clinical_graph,
                    round_number=round_number,
                )
            else:
                normalized = self._normalize_real_response(
                    provider_code=provider_code,
                    content=runtime_result.get("content", ""),
                    clinical_graph=clinical_graph,
                )
            response["normalized_response"] = normalized.as_dict()
            return response
        except ValueError as exc:
            response["status"] = "normalization_failed"
            response["error"] = str(exc)
            response["error_code"] = "normalization_failed"
            response["error_message"] = str(exc)
            response["warnings"].append(
                f"normalization_failed:{provider_code}:repair_attempt_exhausted"
            )
            return response

    def _resolve_provider_execution_mode(
        self,
        provider_code: str,
        requested_execution_mode: str,
    ) -> str:
        if requested_execution_mode in {"mock", "real"}:
            return requested_execution_mode
        return "real" if self.runtime.can_execute_real(provider_code) else "mock"

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
                supported_branch_ids=[
                    branch_index["mechanical_internal"]["id"],
                    branch_index["degenerative"]["id"],
                    branch_index["inflammatory"]["id"],
                ],
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
                supported_branch_ids=[
                    branch_index["mechanical_internal"]["id"],
                    branch_index["inflammatory"]["id"],
                    branch_index["vascular"]["id"],
                ],
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
                supported_branch_ids=[
                    branch_index["mechanical_internal"]["id"],
                    branch_index["referred_pain"]["id"],
                    branch_index["infectious"]["id"],
                ],
                proposed_branches=[provider_candidate],
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
                supported_branch_ids=[
                    branch_index["mechanical_internal"]["id"],
                    branch_index["degenerative"]["id"],
                    branch_index["inflammatory"]["id"],
                    branch_index["vascular"]["id"],
                ],
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
                supported_branch_ids=[
                    branch_index["mechanical_internal"]["id"],
                    branch_index["inflammatory"]["id"],
                    branch_index["vascular"]["id"],
                    branch_index["infectious"]["id"],
                ],
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
                supported_branch_ids=[
                    branch_index["mechanical_internal"]["id"],
                    branch_index["referred_pain"]["id"],
                    branch_index["infectious"]["id"],
                    branch_index["inflammatory"]["id"],
                ],
                proposed_branches=[provider_candidate],
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

    def _normalize_real_response(
        self,
        *,
        provider_code: str,
        content: str,
        clinical_graph: dict,
    ) -> NormalizedClinicalOpinion:
        parsed = self._parse_structured_response(content)
        branch_lookup = {
            branch["id"]: branch
            for branch in clinical_graph["branches"]
        }
        hypotheses: list[dict] = []
        seen_ids: set[str] = set()

        for branch_id in parsed.get("supported_branch_ids", []) + parsed.get("challenged_branch_ids", []):
            branch = branch_lookup.get(branch_id)
            if branch and branch_id not in seen_ids:
                hypotheses.append(branch)
                seen_ids.add(branch_id)

        for item in parsed.get("hypotheses", []):
            if isinstance(item, str):
                branch = branch_lookup.get(item)
                if branch and item not in seen_ids:
                    hypotheses.append(branch)
                    seen_ids.add(item)
                continue
            if not isinstance(item, dict):
                continue
            branch_id = item.get("id")
            if branch_id in branch_lookup and branch_id not in seen_ids:
                hypotheses.append(branch_lookup[branch_id])
                seen_ids.add(branch_id)
            elif branch_id and branch_id not in seen_ids:
                provider_branch = self._provider_branch_from_payload(
                    provider_code=provider_code,
                    payload=item,
                )
                hypotheses.append(provider_branch)
                seen_ids.add(provider_branch["id"])

        proposed_branches = [
            self._provider_branch_from_payload(provider_code=provider_code, payload=item)
            for item in parsed.get("proposed_branches", [])
            if isinstance(item, dict)
        ]
        for proposed in proposed_branches:
            if proposed["id"] not in seen_ids:
                hypotheses.append(proposed)
                seen_ids.add(proposed["id"])

        safety_ids = list(parsed.get("safety_critical_branch_ids", []))
        safety_ids.extend(
            branch["id"]
            for branch in proposed_branches
            if branch.get("safety_critical")
        )
        leading_hypothesis_ids = [
            branch_id
            for branch_id in parsed.get("supported_branch_ids", [])
            if branch_id in branch_lookup
        ][:1]
        if not leading_hypothesis_ids and hypotheses:
            leading_hypothesis_ids = [hypotheses[0]["id"]]

        return NormalizedClinicalOpinion(
            provider_code=provider_code,
            hypotheses=hypotheses,
            leading_hypothesis_ids=leading_hypothesis_ids,
            supported_branch_ids=list(parsed.get("supported_branch_ids", [])),
            challenged_branch_ids=list(parsed.get("challenged_branch_ids", [])),
            proposed_branches=proposed_branches,
            minority_opinions=list(parsed.get("minority_opinions", [])),
            safety_critical_hypothesis_ids=sorted(set(safety_ids)),
            missing_evidence_ids=list(parsed.get("missing_evidence_ids", [])),
            recommended_checks=list(parsed.get("recommended_checks", [])),
            prohibited_conclusions=list(parsed.get("prohibited_conclusions", [])),
            limitations=list(parsed.get("limitations", [])),
            confidence_statement=str(parsed.get("confidence_statement", "")),
            is_mock=False,
        )

    @staticmethod
    def _parse_structured_response(content: str) -> dict:
        candidates = [content, MultiAIConsiliumService._repair_json_payload(content)]
        for candidate in candidates:
            if not candidate:
                continue
            try:
                parsed = json.loads(candidate)
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, dict):
                return parsed
        raise ValueError("normalization_failed")

    @staticmethod
    def _repair_json_payload(content: str) -> str:
        cleaned = content.strip()
        if cleaned.startswith("```"):
            lines = [line for line in cleaned.splitlines() if not line.startswith("```")]
            cleaned = "\n".join(lines).strip()
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            cleaned = cleaned[start:end + 1]
        return cleaned

    @staticmethod
    def _provider_branch_from_payload(provider_code: str, payload: dict) -> dict:
        branch_id = payload.get("id") or payload.get("branch_id") or payload.get("causal_domain") or "provider_branch"
        if ":provider:" not in branch_id:
            branch_id = f"provider:{provider_code}:{branch_id}"
        return {
            "id": branch_id,
            "title": payload.get("title", branch_id),
            "description": payload.get("description", "Provider-proposed branch"),
            "causal_domain": payload.get("causal_domain", branch_id.rsplit(":", maxsplit=1)[-1]),
            "branch_type": payload.get("branch_type", "provider_candidate"),
            "supporting_fact_ids": payload.get("supporting_fact_ids", []),
            "contradicting_fact_ids": payload.get("contradicting_fact_ids", []),
            "missing_evidence_ids": payload.get("missing_evidence_ids", []),
            "evidence_strength": payload.get("evidence_strength", "plausible"),
            "confidence": payload.get("confidence", 0.35),
            "status": payload.get("status", "proposed"),
            "safety_critical": payload.get("safety_critical", False),
            "source": "provider",
            "requires_validation": True,
        }

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
        clinical_graph: dict,
        participant_results: list[dict],
        comparison: dict,
        consensus_mode: str,
        minimum_successful_providers: int,
        requested_provider_count: int,
    ) -> dict:
        successful = [
            result for result in participant_results
            if result["status"] == "completed" and result["normalized_response"] is not None
        ]
        if len(successful) < 2 or len(successful) < minimum_successful_providers:
            consensus_status = "insufficient_participants"
        elif consensus_mode == "strict" and len(successful) < requested_provider_count:
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
            branch["id"]: self._branch_from_snapshot(branch)
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
            for challenged_branch_id in normalized.get("challenged_branch_ids", []):
                branch = branch_lookup.get(challenged_branch_id)
                if branch is None:
                    continue
                reviews.append(
                    BranchReview(
                        role_code=result["provider_code"],
                        branch_id=challenged_branch_id,
                        position=ReviewPosition.WEAKENS,
                        rationale=f"{result['provider_code']} challenged this branch in round {result['round']}",
                        confidence=0.55,
                        provenance=[
                            ProvenanceReference(
                                source_id=f"multi_ai:{result['provider_code']}",
                                source_version=NORMALIZATION_SCHEMA_VERSION,
                                locator=f"round:{result['round']}:challenged",
                            )
                        ],
                    )
                )

        dynamic = self.consilium_service.evaluate(
            clinical_graph["clinical_graph_version"],
            list(branch_lookup.values()),
            roles,
            reviews,
            [],
        )
        summary = dynamic.consensus.summary
        if consensus_status == "insufficient_participants":
            summary = "Multi-provider orchestration did not reach the minimum participant threshold."
        elif consensus_status == "partial_consensus":
            summary = "Partial consensus reached: the leading branch converges, while safety or minority differences remain visible."
        elif consensus_status == "no_consensus":
            summary = "No consensus on a leading branch; alternatives remain visible."

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
        requested_provider_codes: list[str],
        rounds: list[dict],
        comparison: dict,
        consensus: dict,
        execution_mode: str,
        provider_execution_status: str,
    ) -> dict:
        round_one = rounds[0]
        round_one_providers = [item["provider_code"] for item in round_one["responses"]]
        missing_provider_codes = sorted(set(requested_provider_codes) - set(round_one_providers))
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
            "mock_mode_honestly_labeled": not (execution_mode == "mock" and provider_execution_status != "mock_only"),
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
        case_package: dict,
        payload: dict,
    ) -> None:
        round_one = payload["rounds"][0]
        run = self.uow.repo(MultiAIConsiliumRunORM).add(
            MultiAIConsiliumRunORM(
                run_id=run_id,
                case_id=payload["case_id"],
                mode=self._consensus_mode_from_payload(payload),
                execution_mode=payload["execution_mode"],
                requested_provider_codes=payload["requested_providers"],
                successful_provider_codes=payload["successful_providers"],
                failed_provider_codes=payload["failed_providers"],
                case_package=case_package,
                clinical_graph_snapshot=payload["clinical_graph"],
                comparison_snapshot=payload["comparison"],
                devil_review_snapshot=payload["devil_review"],
                consensus_snapshot=payload["consensus"],
                warnings=payload["warnings"],
                limitations=payload["limitations"],
                violations=payload["violations"],
                clinical_graph_version=payload["clinical_graph"]["clinical_graph_version"],
                prompt_version=SYSTEM_PROMPT_VERSION,
                normalization_schema_version=NORMALIZATION_SCHEMA_VERSION,
                comparison_algorithm_version=COMPARISON_ALGORITHM_VERSION,
                consensus_algorithm_version=CONSENSUS_ALGORITHM_VERSION,
                round_one_input_hash=round_one["input_hash"],
                system_prompt_version=SYSTEM_PROMPT_VERSION,
                round_one_prompt_version=ROUND_ONE_PROMPT_VERSION,
                round_two_prompt_version=ROUND_TWO_PROMPT_VERSION,
                devil_prompt_version=DEVIL_PROMPT_VERSION,
                case_package_hash=case_package["case_package_hash"],
            )
        )
        self.uow.session.flush()

        for round_payload in payload["rounds"]:
            for response in round_payload["responses"]:
                self.uow.repo(MultiAIConsiliumParticipantORM).add(
                    MultiAIConsiliumParticipantORM(
                        run_id=run.id,
                        provider_code=response["provider_code"],
                        provider_model=response["provider_model"],
                        execution_mode=response["execution_mode"],
                        round_number=round_payload["round"],
                        independent=response["independent"],
                        prompt_version=response["prompt_version"],
                        input_hash=response["input_hash"],
                        prompt_hash=response["prompt_hash"],
                        model=response["provider_model"],
                        status=response["status"],
                        started_at=self._parse_datetime(response["started_at"]),
                        completed_at=self._parse_datetime(response["completed_at"]),
                        latency_ms=response["latency_ms"],
                        raw_response=response["raw_response"],
                        normalized_response=response["normalized_response"],
                        error=response["error_message"],
                        error_code=response["error_code"],
                        error_message=response["error_message"],
                        fallback_used=response["fallback_used"],
                        is_mock=response["is_mock"],
                        real_provider_call=response["real_provider_call"],
                        attempt_count=response["attempt_count"],
                        usage=response["usage"],
                    )
                )
        self.uow.commit()

    @staticmethod
    def _consensus_mode_from_payload(payload: dict) -> str:
        status = payload["consensus"]["consensus_status"]
        return "strict" if status == "insufficient_participants" else "demo"

    @staticmethod
    def _system_prompt(round_number: int) -> str:
        base_prompt = (
            "You are participating in a structured clinical multi-provider review. "
            "This is not a final diagnosis. Do not hide alternative branches. "
            "Do not close safety-critical branches without sufficient data. "
            "Do not invent sources. Do not convert consensus into proof of causality. "
            "Return valid JSON only with this structure: "
            "{\"hypotheses\": [], \"supported_branch_ids\": [], \"challenged_branch_ids\": [], "
            "\"proposed_branches\": [], \"safety_critical_branch_ids\": [], \"missing_evidence_ids\": [], "
            "\"recommended_checks\": [], \"minority_opinions\": [], \"prohibited_conclusions\": [], "
            "\"limitations\": [], \"confidence_statement\": \"\"}."
        )
        if round_number == 1:
            return base_prompt + " Round 1 is independent: analyze all visible branches yourself."
        return base_prompt + " Round 2 may consider structured disagreement and unresolved safety issues from round 1."

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
    def _branch_from_snapshot(branch: dict) -> HypothesisBranch:
        missing = branch.get("missing_evidence_ids", [])
        supporting = branch.get("supporting_fact_ids", [])
        return HypothesisBranch(
            id=branch["id"],
            case_id=branch["id"].split(":")[0] if ":" in branch["id"] else "CASE",
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
        return MultiAIConsiliumService._hash_text(
            json.dumps(payload, ensure_ascii=False, sort_keys=True)
        )

    @staticmethod
    def _hash_text(value: str) -> str:
        return hashlib.sha256(value.encode("utf-8")).hexdigest()

    @staticmethod
    def _successful_count(participant_results: list[dict]) -> int:
        return sum(
            1
            for result in participant_results
            if result["status"] == "completed" and result["normalized_response"] is not None
        )

    @staticmethod
    def _provider_execution_status(participant_results: list[dict]) -> str:
        execution_modes = {result["execution_mode"] for result in participant_results}
        if execution_modes == {"mock"}:
            return "mock_only"
        if execution_modes == {"real"}:
            return "real_only"
        return "mixed"

    @staticmethod
    def _parse_datetime(value: str | None) -> datetime:
        if not value:
            return datetime.now(timezone.utc)
        return datetime.fromisoformat(value)
