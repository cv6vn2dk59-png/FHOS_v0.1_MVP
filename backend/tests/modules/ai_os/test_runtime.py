import asyncio

import pytest

from app.ai_os.providers.manager import ProviderManager
from app.ai_os.routes import runtime_test
from app.ai_os.runtime import AIRuntime
from app.ai_os.service import runtime_test_request


def test_provider_manager_auto_falls_back_to_openai():
    provider = ProviderManager().get("auto")
    assert provider.__class__.__name__ == "OpenAIProvider"


def test_provider_manager_supports_anthropic_alias():
    provider = ProviderManager().get("anthropic")
    assert provider.__class__.__name__ == "ClaudeProvider"


def test_provider_manager_rejects_unknown_provider():
    with pytest.raises(ValueError):
        ProviderManager().get("unknown")


def test_runtime_execute_uses_requested_provider():
    result = asyncio.run(
        AIRuntime().execute(
            provider="gemini",
            system_prompt="system",
            user_prompt="user",
            temperature=0.2,
        )
    )

    assert result == {
        "provider": "gemini",
        "model": "placeholder",
        "content": "Gemini placeholder",
    }


def test_runtime_test_request_returns_working_payload():
    result = asyncio.run(runtime_test_request())

    assert result["status"] == "ok"
    assert result["provider"] == "openai"
    assert result["runtime"] == "working"
    assert result["response"]["content"] == "OpenAI placeholder"


def test_runtime_route_uses_runtime_service():
    result = asyncio.run(runtime_test("ollama"))

    assert result["provider"] == "ollama"
    assert result["response"]["content"] == "Ollama placeholder"
