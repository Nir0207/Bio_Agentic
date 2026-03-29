from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from typing import Any

import requests

from answering.app.config import Settings
from answering.schemas.render_models import LLMAnswerDraft, PromptBundle

logger = logging.getLogger(__name__)


class LLMUnavailableError(RuntimeError):
    pass


@dataclass
class LLMRunMetadata:
    provider: str
    model_name: str
    fallback_used: bool = False


class LLMClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def generate(self, prompt: PromptBundle) -> tuple[LLMAnswerDraft, LLMRunMetadata]:
        if self.settings.answering_use_fallback_only:
            raise LLMUnavailableError("Fallback-only mode enabled")

        provider = self.settings.answering_provider
        if provider == "openai_compatible":
            return self._openai_compatible(prompt)
        if provider == "azure_openai":
            return self._azure_openai(prompt)
        if provider == "anthropic_compatible":
            return self._anthropic_compatible(prompt)
        if provider == "ollama":
            return self._ollama(prompt)
        raise LLMUnavailableError(f"Unsupported provider: {provider}")

    def _openai_compatible(self, prompt: PromptBundle) -> tuple[LLMAnswerDraft, LLMRunMetadata]:
        base_url = (self.settings.answering_base_url or "https://api.openai.com/v1").rstrip("/")
        api_key = self.settings.answering_api_key
        if not api_key:
            raise LLMUnavailableError("ANSWERING_API_KEY is required for openai_compatible provider")

        payload = {
            "model": self.settings.answering_model_name,
            "temperature": self.settings.answering_temperature,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": prompt.system_prompt},
                {"role": "user", "content": prompt.user_prompt},
            ],
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        data = self._post_with_retries(
            url=f"{base_url}/chat/completions",
            headers=headers,
            payload=payload,
            timeout=self.settings.answering_timeout_seconds,
        )
        content = data["choices"][0]["message"]["content"]
        return self._parse_draft(content), LLMRunMetadata(
            provider="openai_compatible",
            model_name=self.settings.answering_model_name,
        )

    def _azure_openai(self, prompt: PromptBundle) -> tuple[LLMAnswerDraft, LLMRunMetadata]:
        endpoint = (self.settings.azure_openai_endpoint or "").rstrip("/")
        api_key = self.settings.azure_openai_api_key
        if not endpoint or not api_key:
            raise LLMUnavailableError("AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY are required")

        payload = {
            "temperature": self.settings.answering_temperature,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": prompt.system_prompt},
                {"role": "user", "content": prompt.user_prompt},
            ],
        }
        url = (
            f"{endpoint}/openai/deployments/{self.settings.answering_model_name}/chat/completions"
            f"?api-version={self.settings.azure_openai_api_version}"
        )
        headers = {
            "api-key": api_key,
            "Content-Type": "application/json",
        }
        data = self._post_with_retries(
            url=url,
            headers=headers,
            payload=payload,
            timeout=self.settings.answering_timeout_seconds,
        )
        content = data["choices"][0]["message"]["content"]
        return self._parse_draft(content), LLMRunMetadata(
            provider="azure_openai",
            model_name=self.settings.answering_model_name,
        )

    def _anthropic_compatible(self, prompt: PromptBundle) -> tuple[LLMAnswerDraft, LLMRunMetadata]:
        base_url = (self.settings.anthropic_base_url or "https://api.anthropic.com").rstrip("/")
        api_key = self.settings.anthropic_api_key
        if not api_key:
            raise LLMUnavailableError("ANTHROPIC_API_KEY is required for anthropic_compatible provider")

        payload = {
            "model": self.settings.answering_model_name,
            "max_tokens": 900,
            "temperature": self.settings.answering_temperature,
            "system": prompt.system_prompt,
            "messages": [{"role": "user", "content": prompt.user_prompt}],
        }
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        data = self._post_with_retries(
            url=f"{base_url}/v1/messages",
            headers=headers,
            payload=payload,
            timeout=self.settings.answering_timeout_seconds,
        )

        parts = data.get("content") or []
        text_parts = [part.get("text", "") for part in parts if part.get("type") == "text"]
        content = "\n".join(text_parts)
        return self._parse_draft(content), LLMRunMetadata(
            provider="anthropic_compatible",
            model_name=self.settings.answering_model_name,
        )

    def _ollama(self, prompt: PromptBundle) -> tuple[LLMAnswerDraft, LLMRunMetadata]:
        url = f"{self.settings.ollama_base_url.rstrip('/')}/api/chat"
        payload = {
            "model": self.settings.answering_model_name,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": self.settings.answering_temperature,
            },
            "messages": [
                {"role": "system", "content": prompt.system_prompt},
                {"role": "user", "content": prompt.user_prompt},
            ],
        }
        data = self._post_with_retries(
            url=url,
            headers={"Content-Type": "application/json"},
            payload=payload,
            timeout=self.settings.answering_timeout_seconds,
        )
        content = data.get("message", {}).get("content", "")
        return self._parse_draft(content), LLMRunMetadata(
            provider="ollama",
            model_name=self.settings.answering_model_name,
        )

    def _post_with_retries(
        self,
        *,
        url: str,
        headers: dict[str, str],
        payload: dict[str, Any],
        timeout: int,
    ) -> dict[str, Any]:
        attempts = max(1, self.settings.max_retries + 1)
        last_error: Exception | None = None

        for attempt in range(1, attempts + 1):
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=timeout)
                response.raise_for_status()
                return response.json()
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                logger.warning("LLM call attempt %s/%s failed: %s", attempt, attempts, exc)

        raise LLMUnavailableError(f"LLM provider unavailable after retries: {last_error}")

    def _parse_draft(self, content: str) -> LLMAnswerDraft:
        payload = self._extract_json_payload(content)
        return LLMAnswerDraft(
            headline=str(payload.get("headline") or "Grounded answer"),
            answer_text=str(payload.get("answer_text") or ""),
            summary_points=[str(item) for item in payload.get("summary_points", []) if str(item).strip()],
            caveats=[str(item) for item in payload.get("caveats", []) if str(item).strip()],
        )

    @staticmethod
    def _extract_json_payload(content: str) -> dict[str, Any]:
        text = (content or "").strip()
        if not text:
            return {}

        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            return {}

        try:
            parsed = json.loads(match.group(0))
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}
