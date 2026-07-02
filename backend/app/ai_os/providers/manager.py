"""
Provider Manager
"""

from enum import Enum


class Provider(Enum):

    OPENAI = "openai"

    CLAUDE = "claude"

    GEMINI = "gemini"

    OLLAMA = "ollama"


class ProviderManager:

    def __init__(self):

        self.providers = {}

    def register(self, provider_name, provider):

        self.providers[provider_name] = provider

    def get(self, provider_name):

        return self.providers.get(provider_name)


provider_manager = ProviderManager()