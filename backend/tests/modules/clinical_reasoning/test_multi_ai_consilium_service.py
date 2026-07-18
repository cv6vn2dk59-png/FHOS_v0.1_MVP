import asyncio

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.persistence.model_registry  # noqa: F401
from app.application.uow import UnitOfWork
from app.modules.clinical_reasoning.api.routes import multi_ai_consilium
from app.modules.clinical_reasoning.application.multi_ai_consilium_service import (
    MultiAIConsiliumService,
)
from app.modules.clinical_reasoning.persistence.orm import (
    MultiAIConsiliumParticipantORM,
    MultiAIConsiliumRunORM,
)
from app.modules.clinical_reasoning.schemas.multi_ai_consilium import (
    MultiAIConsiliumRequest,
)
from app.persistence.base import Base


def make_uow():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return UnitOfWork(sessionmaker(bind=engine, expire_on_commit=False))


def make_request(**overrides) -> MultiAIConsiliumRequest:
    payload = {
        "case_id": "CASE-KNEE-001",
        "case_text": "болить коліно",
        "provider_codes": ["openai", "claude", "gemini"],
        "clinical_context": {},
        "language": "uk",
        "require_independent_round": True,
        "require_devil_review": True,
        "mode": "demo",
        "minimum_successful_providers": 2,
    }
    payload.update(overrides)
    return MultiAIConsiliumRequest(**payload)


class FakeMixedRuntime:
    def can_execute_real(self, provider: str) -> bool:
        return provider == "openai"

    async def execute(
        self,
        provider: str,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2,
        *,
        execution_mode: str = "mock",
        timeout_seconds: int = 30,
        max_retries: int = 1,
    ) -> dict:
        now = "2026-07-17T00:00:00+00:00"
        if execution_mode == "real":
            return {
                "provider": provider,
                "model": "gpt-5-mini",
                "status": "completed",
                "content": "{\"supported_branch_ids\": [\"KNEE-DEMO-001:branch:mechanical_internal\"], \"challenged_branch_ids\": [], \"proposed_branches\": [], \"safety_critical_branch_ids\": [], \"missing_evidence_ids\": [], \"recommended_checks\": [], \"minority_opinions\": [], \"prohibited_conclusions\": [], \"limitations\": [], \"confidence_statement\": \"real provider\"}",
                "raw_response": {"output_text": "json"},
                "started_at": now,
                "completed_at": now,
                "latency_ms": 10,
                "is_mock": False,
                "real_provider_call": True,
                "fallback_used": False,
                "attempt_count": 1,
                "error_code": None,
                "error_message": None,
                "usage": {"input_tokens": 10, "output_tokens": 5, "total_tokens": 15, "estimated_cost": None, "currency": None},
            }
        return {
            "provider": provider,
            "model": "placeholder",
            "status": "completed",
            "content": f"{provider} placeholder",
            "raw_response": {"content": f"{provider} placeholder"},
            "started_at": now,
            "completed_at": now,
            "latency_ms": 0,
            "is_mock": True,
            "real_provider_call": False,
            "fallback_used": False,
            "attempt_count": 0,
            "error_code": None,
            "error_message": None,
            "usage": None,
        }


def test_multi_ai_consilium_builds_mock_knee_orchestration_with_consistent_round_one_input():
    with make_uow() as uow:
        payload = asyncio.run(MultiAIConsiliumService(uow).run(make_request()))

        assert payload["execution_mode"] == "mock"
        assert payload["is_mock"] is True
        assert payload["real_provider_calls"] is False
        assert payload["provider_execution_status"] == "mock_only"
        assert payload["clinical_graph"]["symptom"] == "болить коліно"
        assert payload["clinical_graph"]["clinical_graph_source"] == "deterministic_fhos"
        assert [item["provider_code"] for item in payload["participants"]] == [
            "openai",
            "claude",
            "gemini",
        ]
        assert all(item["status"] == "completed" for item in payload["participants"])
        assert all(item["is_mock"] is True for item in payload["participants"])
        assert all(item["fallback_used"] is False for item in payload["participants"])
        assert payload["rounds"][0]["round"] == 1
        assert payload["rounds"][0]["independent"] is True
        assert len({item["input_hash"] for item in payload["rounds"][0]["responses"]}) == 1
        assert all(item["prompt_version"] == "multi-ai-round-one.v1" for item in payload["rounds"][0]["responses"])
        assert payload["comparison"]["agreements"]["leading_hypothesis_ids"] == [
            "KNEE-DEMO-001:branch:mechanical_internal"
        ]
        assert payload["consensus"]["consensus_status"] == "partial_consensus"


def test_multi_ai_consilium_preserves_round_one_and_persists_versions():
    with make_uow() as uow:
        payload = asyncio.run(MultiAIConsiliumService(uow).run(make_request()))

        assert len(payload["rounds"]) == 2
        assert payload["rounds"][1]["round"] == 2
        assert payload["rounds"][1]["independent"] is False

        round_one_openai = next(
            item for item in payload["rounds"][0]["responses"] if item["provider_code"] == "openai"
        )
        round_two_openai = next(
            item for item in payload["rounds"][1]["responses"] if item["provider_code"] == "openai"
        )
        assert len(round_one_openai["normalized_response"]["hypotheses"]) == 3
        assert len(round_two_openai["normalized_response"]["hypotheses"]) == 4
        assert len(payload["rounds"][0]["responses"]) == 3

        run = uow.repo(MultiAIConsiliumRunORM).by_run_id(payload["run_id"])
        assert run is not None
        assert run.case_id == "CASE-KNEE-001"
        assert run.execution_mode == "mock"
        assert run.clinical_graph_version == "deterministic-fhos-knee.v1"
        assert run.comparison_algorithm_version == "multi-ai-comparison.v2"
        assert len(run.round_one_input_hash) == 64

        participants = uow.session.query(MultiAIConsiliumParticipantORM).all()
        assert len(participants) == 6
        assert sorted({item.round_number for item in participants}) == [1, 2]
        assert {item.prompt_version for item in participants} == {
            "multi-ai-round-one.v1",
            "multi-ai-round-two.v1",
        }


def test_multi_ai_consilium_surfaces_unique_provider_safety_branch_and_devil_review_keeps_it():
    with make_uow() as uow:
        payload = asyncio.run(MultiAIConsiliumService(uow).run(make_request()))

        unique_safety = next(
            item
            for item in payload["comparison"]["unique_hypotheses"]
            if item["branch_id"] == "KNEE-DEMO-001:provider:gemini:acute_neurovascular_red_flag"
        )
        assert unique_safety["providers"] == ["gemini"]
        assert unique_safety["safety_critical"] is True
        assert unique_safety["status"] == "proposed"
        assert unique_safety["source"] == "provider"
        assert unique_safety["requires_validation"] is True
        assert any(
            item["risk"] == "unique_provider_safety_branch"
            and item["provider_codes"] == ["gemini"]
            for item in payload["devil_review"]["findings"]
        )
        assert payload["devil_review"]["checks"]["round_one_input_hash_consistent"] is True
        assert payload["devil_review"]["checks"]["round_one_is_independent"] is True


def test_multi_ai_consilium_strict_mode_exposes_failure_without_hidden_fallback():
    with make_uow() as uow:
        payload = asyncio.run(
            MultiAIConsiliumService(uow).run(
                make_request(
                    mode="strict",
                    forced_failure_provider_codes=["claude"],
                )
            )
        )

        failed = next(item for item in payload["rounds"][0]["responses"] if item["provider_code"] == "claude")
        assert failed["status"] == "failed"
        assert failed["error"] == "forced_failure_for_test"
        assert failed["fallback_used"] is False
        assert payload["comparison"]["provider_failures"] == [
            {
                "provider_code": "claude",
                "status": "failed",
                "error": "forced_failure_for_test",
            }
        ]
        assert payload["consensus"]["consensus_status"] == "insufficient_participants"


def test_multi_ai_consilium_quorum_mode_allows_partial_consensus_after_failure():
    with make_uow() as uow:
        payload = asyncio.run(
            MultiAIConsiliumService(uow).run(
                make_request(
                    mode="quorum",
                    require_independent_round=False,
                    minimum_successful_providers=2,
                    forced_failure_provider_codes=["claude"],
                )
            )
        )

        assert len(payload["rounds"]) == 1
        assert payload["consensus"]["consensus_status"] == "partial_consensus"
        assert payload["devil_review"]["status"] == "failed"
        assert any(
            item["risk"] == "unique_provider_safety_branch"
            for item in payload["devil_review"]["findings"]
        )


def test_multi_ai_consilium_repeat_runs_create_new_run_ids():
    with make_uow() as uow:
        first = asyncio.run(MultiAIConsiliumService(uow).run(make_request()))
        second = asyncio.run(MultiAIConsiliumService(uow).run(make_request()))

        assert first["run_id"] != second["run_id"]


def test_multi_ai_consilium_route_returns_serializable_payload():
    with make_uow() as uow:
        payload = asyncio.run(multi_ai_consilium(make_request(), uow))

        assert payload["case_id"] == "CASE-KNEE-001"
        assert payload["execution_mode"] == "mock"
        assert payload["participants"][0]["provider_code"] == "openai"
        assert payload["devil_review"]["status"] == "failed"


def test_multi_ai_consilium_marks_mixed_execution_explicitly():
    with make_uow() as uow:
        payload = asyncio.run(
            MultiAIConsiliumService(
                uow,
                runtime=FakeMixedRuntime(),
            ).run(
                make_request(
                    execution_mode="mixed",
                    require_round_two=False,
                )
            )
        )

        assert payload["provider_execution_status"] == "mixed"
        assert payload["is_mock"] is True
        assert payload["real_provider_calls"] is True
        assert "openai" in payload["successful_providers"]
