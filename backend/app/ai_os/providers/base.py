"""
Base LLM Provider
"""

from __future__ import annotations

import asyncio
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from urllib import error, request

from app.core.config import get_settings


@dataclass(frozen=True)
class ProviderError(Exception):
    code: str
    message: str
    retryable: bool = False

    def __str__(self) -> str:
        return self.message


class BaseProvider(ABC):
    provider_code = "provider"
    api_key_setting = ""
    model_setting = ""
    default_base_url = ""
    mock_content_label = "Provider"

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2,
        *,
        execution_mode: str = "mock",
        timeout_seconds: int = 30,
        max_retries: int = 1,
    ) -> dict:
        if execution_mode == "mock":
            return self._mock_result()

        if not self.is_configured():
            return self._failed_result(
                model=self.configured_model(),
                error_code="provider_not_configured",
                error_message=f"{self.provider_code} is not configured",
                attempt_count=0,
                is_mock=(execution_mode == "mixed"),
            )

        attempt_count = 0
        last_error: ProviderError | None = None
        max_attempts = max(1, max_retries + 1)
        while attempt_count < max_attempts:
            attempt_count += 1
            started_at = datetime.now(timezone.utc)
            try:
                raw_response = await self._generate_real(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    temperature=temperature,
                    timeout_seconds=timeout_seconds,
                )
                completed_at = datetime.now(timezone.utc)
                usage = self._extract_usage(raw_response)
                content = self._extract_content(raw_response)
                return {
                    "provider": self.provider_code,
                    "model": self._extract_model(raw_response),
                    "status": "completed",
                    "content": content,
                    "raw_response": raw_response,
                    "started_at": started_at.isoformat(),
                    "completed_at": completed_at.isoformat(),
                    "latency_ms": self._latency_ms(started_at, completed_at),
                    "is_mock": False,
                    "real_provider_call": True,
                    "fallback_used": False,
                    "attempt_count": attempt_count,
                    "error_code": None,
                    "error_message": None,
                    "usage": usage,
                }
            except ProviderError as exc:
                last_error = exc
                if not exc.retryable or attempt_count >= max_attempts:
                    break

        return self._failed_result(
            model=self.configured_model(),
            error_code=last_error.code if last_error else "provider_error",
            error_message=str(last_error) if last_error else f"{self.provider_code} failed",
            attempt_count=attempt_count,
            is_mock=False,
        )

    def status_snapshot(self, *, reachable: bool | None = None, last_error_type: str | None = None) -> dict:
        return {
            "provider_code": self.provider_code,
            "configured": self.is_configured(),
            "model": self.configured_model(),
            "reachable": reachable,
            "last_check_at": None,
            "last_error_type": last_error_type,
        }

    def is_configured(self) -> bool:
        api_key = self._read_setting(self.api_key_setting)
        return bool(api_key) if self.api_key_setting else True

    def configured_model(self) -> str:
        model = self._read_setting(self.model_setting)
        return model or "placeholder"

    async def _generate_real(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        timeout_seconds: int,
    ) -> dict:
        raise NotImplementedError

    async def _post_json(
        self,
        *,
        url: str,
        headers: dict[str, str],
        body: dict[str, Any],
        timeout_seconds: int,
    ) -> dict:
        payload = json.dumps(body).encode("utf-8")
        return await asyncio.to_thread(
            self._post_json_sync,
            url,
            headers,
            payload,
            timeout_seconds,
        )

    def _post_json_sync(
        self,
        url: str,
        headers: dict[str, str],
        payload: bytes,
        timeout_seconds: int,
    ) -> dict:
        http_request = request.Request(
            url=url,
            data=payload,
            headers=headers,
            method="POST",
        )
        try:
            with request.urlopen(http_request, timeout=timeout_seconds) as response:
                return json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise self._map_http_error(exc.code, body) from exc
        except error.URLError as exc:
            raise ProviderError(
                code="network_error",
                message=f"{self.provider_code} network error: {exc.reason}",
                retryable=True,
            ) from exc
        except TimeoutError as exc:
            raise ProviderError(
                code="timeout",
                message=f"{self.provider_code} request timed out",
                retryable=True,
            ) from exc

    def _map_http_error(self, status_code: int, body: str) -> ProviderError:
        lowered = body.lower()
        if status_code in {408, 429, 500, 502, 503, 504}:
            return ProviderError(
                code=f"http_{status_code}",
                message=f"{self.provider_code} temporary HTTP error {status_code}",
                retryable=True,
            )
        if "api key" in lowered or "unauthorized" in lowered or status_code in {401, 403}:
            return ProviderError(
                code="invalid_api_key",
                message=f"{self.provider_code} rejected the API credentials",
                retryable=False,
            )
        if "model" in lowered and status_code == 404:
            return ProviderError(
                code="invalid_model",
                message=f"{self.provider_code} model was not found",
                retryable=False,
            )
        return ProviderError(
            code=f"http_{status_code}",
            message=f"{self.provider_code} HTTP error {status_code}",
            retryable=False,
        )

    def _extract_usage(self, raw_response: dict) -> dict | None:
        return None

    def _extract_model(self, raw_response: dict) -> str:
        return raw_response.get("model", self.configured_model())

    @abstractmethod
    def _extract_content(self, raw_response: dict) -> str:
        raise NotImplementedError

    def _mock_result(self) -> dict:
        now = datetime.now(timezone.utc).isoformat()
        return {
            "provider": self.provider_code,
            "model": "placeholder",
            "status": "completed",
            "content": f"{self.mock_content_label} placeholder",
            "raw_response": {
                "provider": self.provider_code,
                "model": "placeholder",
                "content": f"{self.mock_content_label} placeholder",
            },
            "started_at": now,
            "completed_at": now,
            "latency_ms": 0,
            "is_mock": True,
            "real_provider_call": False,
            "fallback_used": False,
            "attempt_count": 0,
            "error_code": None,
            "error_message": None,
            "usage": None,
        }

    def _failed_result(
        self,
        *,
        model: str,
        error_code: str,
        error_message: str,
        attempt_count: int,
        is_mock: bool,
    ) -> dict:
        now = datetime.now(timezone.utc).isoformat()
        return {
            "provider": self.provider_code,
            "model": model,
            "status": "failed",
            "content": "",
            "raw_response": None,
            "started_at": now,
            "completed_at": now,
            "latency_ms": 0,
            "is_mock": is_mock,
            "real_provider_call": False,
            "fallback_used": False,
            "attempt_count": attempt_count,
            "error_code": error_code,
            "error_message": error_message,
            "usage": None,
        }

    @staticmethod
    def _latency_ms(started_at: datetime, completed_at: datetime) -> int:
        return int((completed_at - started_at).total_seconds() * 1000)

    @staticmethod
    def _read_setting(field_name: str) -> Any:
        settings = get_settings()
        return getattr(settings, field_name, None)
