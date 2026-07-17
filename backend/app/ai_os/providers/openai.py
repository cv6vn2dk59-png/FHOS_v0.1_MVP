from .base import BaseProvider


class OpenAIProvider(BaseProvider):
    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2,
    ) -> dict:
        return {
            "provider": "openai",
            "model": "placeholder",
            "content": "OpenAI placeholder",
        }
