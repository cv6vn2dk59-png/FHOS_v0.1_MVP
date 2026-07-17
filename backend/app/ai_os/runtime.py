"""
AI Runtime layer for provider-routed execution.
"""

from app.ai_os.providers.manager import ProviderManager


class AIRuntime:
    def __init__(self, provider_manager: ProviderManager | None = None):
        self.provider_manager = provider_manager or ProviderManager()

    async def execute(
        self,
        provider: str,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2,
    ) -> dict:
        selected_provider = self.provider_manager.get(provider)
        return await selected_provider.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
        )
