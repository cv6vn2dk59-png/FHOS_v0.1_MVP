"""
Provider Manager
"""

from __future__ import annotations

from enum import Enum

from app.ai_os.providers.anthropic import ClaudeProvider
from app.ai_os.providers.gemini import GeminiProvider
from app.ai_os.providers.openai import OpenAIProvider
from app.ai_os.providers.ollama import OllamaProvider


class Provider(Enum):
    OPENAI = "openai"
    CLAUDE = "claude"
    GEMINI = "gemini"
    OLLAMA = "ollama"


class ProviderManager:
    def __init__(self):
        self.providers = {
            Provider.OPENAI.value: OpenAIProvider(),
            Provider.CLAUDE.value: ClaudeProvider(),
            Provider.GEMINI.value: GeminiProvider(),
            Provider.OLLAMA.value: OllamaProvider(),
        }

    def register(self, provider_name: str, provider) -> None:
        self.providers[provider_name] = provider

    def get(self, provider_name: str):
        normalized_name = self.normalize(provider_name)
        provider = self.providers.get(normalized_name)
        if provider is None:
            supported = ", ".join(sorted(["auto", *self.providers.keys()]))
            raise ValueError(
                f"Unsupported provider '{provider_name}'. Supported providers: {supported}"
            )
        return provider

    def normalize(self, provider_name: str) -> str:
        normalized_name = (provider_name or "auto").strip().lower()
        if normalized_name == "auto":
            normalized_name = Provider.OPENAI.value
        if normalized_name == "anthropic":
            normalized_name = Provider.CLAUDE.value
        return normalized_name

    def can_execute_real(self, provider_name: str) -> bool:
        return self.get(provider_name).is_configured()

    def status_snapshot(self) -> list[dict]:
        return [
            self.providers[key].status_snapshot()
            for key in sorted(self.providers)
        ]


provider_manager = ProviderManager()
