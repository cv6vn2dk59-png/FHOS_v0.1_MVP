import asyncio

from app.ai_os.providers.anthropic import ClaudeProvider
from app.ai_os.providers.base import ProviderError
from app.ai_os.providers.gemini import GeminiProvider
from app.ai_os.providers.ollama import OllamaProvider
from app.ai_os.providers.openai import OpenAIProvider
from app.ai_os.service import ai_os_status
from app.core.config import get_settings


def test_openai_provider_builds_real_request(monkeypatch):
    captured = {}
    provider = OpenAIProvider()
    get_settings.cache_clear()
    monkeypatch.setenv("OPENAI_API_KEY", "secret-openai")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-5-mini")

    async def fake_post_json(*, url, headers, body, timeout_seconds):
        captured["url"] = url
        captured["headers"] = headers
        captured["body"] = body
        captured["timeout_seconds"] = timeout_seconds
        return {
            "model": "gpt-5-mini",
            "output_text": "{\"supported_branch_ids\": []}",
            "usage": {"input_tokens": 10, "output_tokens": 5, "total_tokens": 15},
        }

    monkeypatch.setattr(provider, "_post_json", fake_post_json)
    result = asyncio.run(
        provider.generate(
            system_prompt="system",
            user_prompt="user",
            execution_mode="real",
            timeout_seconds=12,
        )
    )

    assert captured["url"] == "https://api.openai.com/v1/responses"
    assert captured["headers"]["Authorization"] == "Bearer secret-openai"
    assert captured["body"]["model"] == "gpt-5-mini"
    assert captured["body"]["input"][0]["role"] == "system"
    assert result["status"] == "completed"
    assert result["usage"]["total_tokens"] == 15


def test_claude_provider_builds_real_request(monkeypatch):
    captured = {}
    provider = ClaudeProvider()
    get_settings.cache_clear()
    monkeypatch.setenv("ANTHROPIC_API_KEY", "secret-claude")
    monkeypatch.setenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")

    async def fake_post_json(*, url, headers, body, timeout_seconds):
        captured["url"] = url
        captured["headers"] = headers
        captured["body"] = body
        return {
            "model": "claude-sonnet-4-20250514",
            "content": [{"type": "text", "text": "{\"supported_branch_ids\": []}"}],
            "usage": {"input_tokens": 7, "output_tokens": 3},
        }

    monkeypatch.setattr(provider, "_post_json", fake_post_json)
    result = asyncio.run(provider.generate("system", "user", execution_mode="real"))

    assert captured["url"] == "https://api.anthropic.com/v1/messages"
    assert captured["headers"]["x-api-key"] == "secret-claude"
    assert captured["body"]["system"] == "system"
    assert captured["body"]["messages"][0]["content"] == "user"
    assert result["usage"]["total_tokens"] == 10


def test_gemini_provider_builds_real_request(monkeypatch):
    captured = {}
    provider = GeminiProvider()
    get_settings.cache_clear()
    monkeypatch.setenv("GEMINI_API_KEY", "secret-gemini")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-3.5-flash")

    async def fake_post_json(*, url, headers, body, timeout_seconds):
        captured["url"] = url
        captured["headers"] = headers
        captured["body"] = body
        return {
            "candidates": [{"content": {"parts": [{"text": "{\"supported_branch_ids\": []}"}]}}],
            "usageMetadata": {"promptTokenCount": 6, "candidatesTokenCount": 4, "totalTokenCount": 10},
        }

    monkeypatch.setattr(provider, "_post_json", fake_post_json)
    result = asyncio.run(provider.generate("system", "user", execution_mode="real"))

    assert captured["url"].endswith("/models/gemini-3.5-flash:generateContent")
    assert captured["headers"]["x-goog-api-key"] == "secret-gemini"
    assert captured["body"]["system_instruction"]["parts"][0]["text"] == "system"
    assert result["usage"]["total_tokens"] == 10


def test_ollama_provider_builds_real_request(monkeypatch):
    captured = {}
    provider = OllamaProvider()
    get_settings.cache_clear()
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:11434/api")
    monkeypatch.setenv("OLLAMA_MODEL", "llama3.1")

    async def fake_post_json(*, url, headers, body, timeout_seconds):
        captured["url"] = url
        captured["headers"] = headers
        captured["body"] = body
        return {
            "model": "llama3.1",
            "response": "{\"supported_branch_ids\": []}",
            "prompt_eval_count": 9,
            "eval_count": 3,
        }

    monkeypatch.setattr(provider, "_post_json", fake_post_json)
    result = asyncio.run(provider.generate("system", "user", execution_mode="real"))

    assert captured["url"] == "http://localhost:11434/api/generate"
    assert captured["body"]["model"] == "llama3.1"
    assert captured["body"]["stream"] is False
    assert result["usage"]["total_tokens"] == 12


def test_retry_happens_only_for_retryable_errors(monkeypatch):
    provider = OpenAIProvider()
    get_settings.cache_clear()
    monkeypatch.setenv("OPENAI_API_KEY", "secret-openai")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-5-mini")
    attempts = {"count": 0}

    async def flaky_generate_real(**kwargs):
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise ProviderError(code="timeout", message="temporary timeout", retryable=True)
        return {
            "model": "gpt-5-mini",
            "output_text": "{\"supported_branch_ids\": []}",
            "usage": {"input_tokens": 1, "output_tokens": 1, "total_tokens": 2},
        }

    monkeypatch.setattr(provider, "_generate_real", flaky_generate_real)
    result = asyncio.run(provider.generate("system", "user", execution_mode="real", max_retries=1))

    assert attempts["count"] == 2
    assert result["status"] == "completed"


def test_invalid_api_key_does_not_retry(monkeypatch):
    provider = OpenAIProvider()
    get_settings.cache_clear()
    monkeypatch.setenv("OPENAI_API_KEY", "secret-openai")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-5-mini")
    attempts = {"count": 0}

    async def bad_generate_real(**kwargs):
        attempts["count"] += 1
        raise ProviderError(code="invalid_api_key", message="bad key", retryable=False)

    monkeypatch.setattr(provider, "_generate_real", bad_generate_real)
    result = asyncio.run(provider.generate("system", "user", execution_mode="real", max_retries=1))

    assert attempts["count"] == 1
    assert result["status"] == "failed"
    assert result["error_code"] == "invalid_api_key"


def test_ai_os_status_shows_provider_configuration_without_keys(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("OPENAI_API_KEY", "secret-openai")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-5-mini")

    payload = ai_os_status()

    assert "providers" in payload
    openai_status = next(item for item in payload["providers"] if item["provider_code"] == "openai")
    assert openai_status["configured"] is True
    assert openai_status["model"] == "gpt-5-mini"
    assert "api_key" not in str(payload).lower()
