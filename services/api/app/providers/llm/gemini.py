"""Real Google Gemini structured-output provider with key-pool rotation and cooldown. Owner: Backend."""

from __future__ import annotations

import json
import logging
import time
from typing import Any

from app.providers.llm.base import LLMProvider, LLMProviderUnavailable, LLMUsage

logger = logging.getLogger(__name__)

_RATE_LIMIT_COOLDOWN_SECONDS = 60.0
_INVALID_KEY_COOLDOWN_SECONDS = 3600.0


class _KeySlot:
    """One pooled API key plus its lazily-built client and health state."""

    def __init__(self, key: str) -> None:
        self.key = key
        self.client: Any | None = None
        self.cooldown_until: float = 0.0
        self.success_count = 0
        self.failure_count = 0
        self.last_error: str | None = None


class GeminiLLMProvider(LLMProvider):
    """Round-robin, cooldown-aware Gemini provider over a pool of API keys."""

    def __init__(self, api_keys: list[str], model: str) -> None:
        if not api_keys:
            raise RuntimeError("GeminiLLMProvider requires at least one API key")
        self._model = model
        self._slots = [_KeySlot(key) for key in api_keys]
        self._next_index = 0

    def _client_for(self, slot: _KeySlot) -> Any:
        if slot.client is None:
            from google import genai

            slot.client = genai.Client(api_key=slot.key)
        return slot.client

    def key_health(self) -> list[dict[str, Any]]:
        """Per-key health metrics. Only the last 4 characters of each key are included."""
        now = time.monotonic()
        return [
            {
                "key_suffix": slot.key[-4:],
                "success_count": slot.success_count,
                "failure_count": slot.failure_count,
                "cooling_down": slot.cooldown_until > now,
                "last_error": slot.last_error,
            }
            for slot in self._slots
        ]

    def generate_structured(
        self,
        schema: dict[str, Any],
        messages: list[dict[str, str]],
        opts: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        from google.genai import errors, types

        prompt = "\n\n".join(f"[{m['role']}] {m['content']}" for m in messages)
        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_json_schema=schema,
        )

        now = time.monotonic()
        start = self._next_index
        self._next_index = (self._next_index + 1) % len(self._slots)
        order = self._slots[start:] + self._slots[:start]

        last_exc: Exception | None = None
        for slot in order:
            if slot.cooldown_until > now:
                continue
            client = self._client_for(slot)
            try:
                response = client.models.generate_content(
                    model=self._model, contents=prompt, config=config
                )
            except errors.APIError as exc:
                slot.failure_count += 1
                slot.last_error = f"{exc.code} {exc.status}"
                last_exc = exc
                if exc.code == 429 or isinstance(exc, errors.ServerError):
                    slot.cooldown_until = now + _RATE_LIMIT_COOLDOWN_SECONDS
                    continue
                if exc.code in (401, 403):
                    slot.cooldown_until = now + _INVALID_KEY_COOLDOWN_SECONDS
                    continue
                raise
            except Exception as exc:
                slot.failure_count += 1
                slot.last_error = str(exc)
                last_exc = exc
                slot.cooldown_until = now + _RATE_LIMIT_COOLDOWN_SECONDS
                continue
            else:
                slot.success_count += 1
                usage = getattr(response, "usage_metadata", None)
                self.last_usage = (
                    LLMUsage(
                        input_tokens=usage.prompt_token_count,
                        output_tokens=usage.candidates_token_count,
                        total_tokens=usage.total_token_count,
                    )
                    if usage is not None
                    else None
                )
                return json.loads(response.text)

        if last_exc is not None:
            raise LLMProviderUnavailable(
                f"All Gemini keys in the pool are rate-limited or unavailable: {last_exc}"
            ) from last_exc
        raise LLMProviderUnavailable("All Gemini API keys are cooling down; no healthy key available")
