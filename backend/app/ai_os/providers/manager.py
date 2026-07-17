"""
Provider Manager
"""

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
        normalized_name = (provider_name or "auto").strip().lower()
        if normalized_name == "auto":
            normalized_name = Provider.OPENAI.value
        if normalized_name == "anthropic":
            normalized_name = Provider.CLAUDE.value

        provider = self.providers.get(normalized_name)
        if provider is None:
            supported = ", ".join(sorted(["auto", *self.providers.keys()]))
            raise ValueError(
                f"Unsupported provider '{provider_name}'. Supported providers: {supported}"
            )
        return provider


provider_manager = ProviderManager()
