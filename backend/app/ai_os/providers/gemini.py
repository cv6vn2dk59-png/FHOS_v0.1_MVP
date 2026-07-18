from __future__ import annotations

from app.ai_os.providers.base import BaseProvider


class GeminiProvider(BaseProvider):
    provider_code = "gemini"
    api_key_setting = "gemini_api_key"
    model_setting = "gemini_model"
    mock_content_label = "Gemini"

    async def _generate_real(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        timeout_seconds: int,
    ) -> dict:
        model = self.configured_model()
        return await self._post_json(
            url=f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
            headers={
                "x-goog-api-key": self._read_setting(self.api_key_setting),
                "Content-Type": "application/json",
            },
            body={
                "system_instruction": {
                    "parts": [
                        {
                            "text": system_prompt,
                        }
                    ]
                },
                "contents": [
                    {
                        "role": "user",
                        "parts": [
                            {
                                "text": user_prompt,
                            }
                        ],
                    }
                ],
                "generationConfig": {
                    "temperature": temperature,
                },
            },
            timeout_seconds=timeout_seconds,
        )

    def _extract_content(self, raw_response: dict) -> str:
        candidates = raw_response.get("candidates", [])
        if not candidates:
            return ""
        parts = candidates[0].get("content", {}).get("parts", [])
        texts = [part.get("text", "") for part in parts if part.get("text")]
        return "\n".join(texts)

    def _extract_usage(self, raw_response: dict) -> dict | None:
        usage = raw_response.get("usageMetadata")
        if not usage:
            return None
        return {
            "input_tokens": usage.get("promptTokenCount"),
            "output_tokens": usage.get("candidatesTokenCount"),
            "total_tokens": usage.get("totalTokenCount"),
            "estimated_cost": None,
            "currency": None,
        }
