from .base import BaseProvider


class GeminiProvider(BaseProvider):

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2,
    ) -> dict:

        return {
            "provider": "gemini",
            "status": "ok",
            "response": "Gemini placeholder",
        }