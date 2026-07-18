from __future__ import annotations

from app.ai_os.providers.base import BaseProvider


class OllamaProvider(BaseProvider):
    provider_code = "ollama"
    model_setting = "ollama_model"
    mock_content_label = "Ollama"

    async def _generate_real(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        timeout_seconds: int,
    ) -> dict:
        base_url = (self._read_setting("ollama_base_url") or self.default_base_url or "http://localhost:11434/api").rstrip("/")
        return await self._post_json(
            url=f"{base_url}/generate",
            headers={
                "Content-Type": "application/json",
            },
            body={
                "model": self.configured_model(),
                "system": system_prompt,
                "prompt": user_prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                },
            },
            timeout_seconds=timeout_seconds,
        )

    def _extract_content(self, raw_response: dict) -> str:
        return raw_response.get("response", "")

    def _extract_usage(self, raw_response: dict) -> dict | None:
        input_tokens = raw_response.get("prompt_eval_count")
        output_tokens = raw_response.get("eval_count")
        total_tokens = None
        if input_tokens is not None or output_tokens is not None:
            total_tokens = (input_tokens or 0) + (output_tokens or 0)
        return {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "estimated_cost": None,
            "currency": None,
        }
