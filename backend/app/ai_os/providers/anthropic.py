from __future__ import annotations

from app.ai_os.providers.base import BaseProvider


class ClaudeProvider(BaseProvider):
    provider_code = "claude"
    api_key_setting = "anthropic_api_key"
    model_setting = "anthropic_model"
    mock_content_label = "Claude"

    async def _generate_real(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        timeout_seconds: int,
    ) -> dict:
        return await self._post_json(
            url="https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": self._read_setting(self.api_key_setting),
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            body={
                "model": self.configured_model(),
                "max_tokens": 2048,
                "temperature": temperature,
                "system": system_prompt,
                "messages": [
                    {
                        "role": "user",
                        "content": user_prompt,
                    }
                ],
            },
            timeout_seconds=timeout_seconds,
        )

    def _extract_content(self, raw_response: dict) -> str:
        parts = []
        for item in raw_response.get("content", []):
            text = item.get("text")
            if text:
                parts.append(text)
        return "\n".join(parts)

    def _extract_usage(self, raw_response: dict) -> dict | None:
        usage = raw_response.get("usage")
        if not usage:
            return None
        input_tokens = usage.get("input_tokens")
        output_tokens = usage.get("output_tokens")
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
