from .base import BaseProvider


class OllamaProvider(BaseProvider):

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2,
    ) -> dict:

        return {
            "provider": "ollama",
            "status": "ok",
            "response": "Ollama placeholder",
        }