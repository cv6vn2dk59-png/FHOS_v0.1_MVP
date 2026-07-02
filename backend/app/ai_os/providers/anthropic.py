from .base import BaseProvider


class ClaudeProvider(BaseProvider):

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2,
    ) -> dict:

        return {
            "provider": "claude",
            "status": "ok",
            "response": "Claude placeholder",
        }