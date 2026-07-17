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
            "model": "placeholder",
            "content": "Ollama placeholder",
        }
