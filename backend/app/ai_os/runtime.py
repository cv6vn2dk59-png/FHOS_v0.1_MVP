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
        *,
        execution_mode: str = "mock",
        timeout_seconds: int = 30,
        max_retries: int = 1,
    ) -> dict:
        selected_provider = self.provider_manager.get(provider)
        return await selected_provider.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            execution_mode=execution_mode,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
        )

    def can_execute_real(self, provider: str) -> bool:
        return self.provider_manager.can_execute_real(provider)

    def provider_status(self) -> list[dict]:
        return self.provider_manager.status_snapshot()
