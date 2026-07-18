from __future__ import annotations

from app.ai_os.providers.base import BaseProvider


class OpenAIProvider(BaseProvider):
    provider_code = "openai"
    api_key_setting = "openai_api_key"
    model_setting = "openai_model"
    mock_content_label = "OpenAI"

    async def _generate_real(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        timeout_seconds: int,
    ) -> dict:
        return await self._post_json(
            url="https://api.openai.com/v1/responses",
            headers={
                "Authorization": f"Bearer {self._read_setting(self.api_key_setting)}",
                "Content-Type": "application/json",
            },
            body={
                "model": self.configured_model(),
                "temperature": temperature,
                "input": [
                    {
                        "role": "system",
                        "content": [{"type": "input_text", "text": system_prompt}],
                    },
                    {
                        "role": "user",
                        "content": [{"type": "input_text", "text": user_prompt}],
                    },
                ],
            },
            timeout_seconds=timeout_seconds,
        )

    def _extract_content(self, raw_response: dict) -> str:
        if raw_response.get("output_text"):
            return raw_response["output_text"]
        outputs = []
        for item in raw_response.get("output", []):
            for content in item.get("content", []):
                text = content.get("text")
                if text:
                    outputs.append(text)
        return "\n".join(outputs)

    def _extract_usage(self, raw_response: dict) -> dict | None:
        usage = raw_response.get("usage")
        if not usage:
            return None
        return {
            "input_tokens": usage.get("input_tokens"),
            "output_tokens": usage.get("output_tokens"),
            "total_tokens": usage.get("total_tokens"),
            "estimated_cost": None,
            "currency": None,
        }
