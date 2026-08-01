"""Real Google Gemini structured-output provider. Owner: Backend.

Only file in the repo allowed to import google.genai (hard constraint,
guidelines.md §9.3 / techstack.md §11.1). AIA/AIS call
`LLMProvider.generate_structured()` through DI — never this class
directly.

Uses google.genai (not the deprecated google.generativeai) and
`response_json_schema` (not `response_schema`). Reasons, found live
against a real key while wiring B1 (docs/work.md):

- Pydantic's `.model_json_schema()` emits `$defs`/`$ref` for any schema
  with a nested model (e.g. IdentityAttribute -> IdentityMarker, used by
  the onboarding extraction schema). google.generativeai's
  `response_schema` (a flattened OpenAPI-subset proto) rejects those
  keys client-side with `ValueError: Unknown field for Schema: $defs`
  before any network call is made — every structured call with a nested
  schema fails unconditionally, not just intermittently.
- google.genai's `response_json_schema` field explicitly documents
  support for `$id`/`$defs`/`$ref`/`$anchor` (see
  `google.genai.types.GenerateContentConfig`); verified with a real
  nested-schema call against the live API before this file was written.

Key rotation (docs/work.md B2): a pool of keys is round-robined across
calls; a key that fails with a rate-limit (429) or server error (5xx)
is put in cooldown and the call retries the next healthy key in the
pool, so one exhausted/unhealthy key does not take the whole provider
down. An invalid-credential error (401/403) cools that key down for
much longer, since retrying it sooner cannot help. A malformed-request
error (anything else, e.g. a schema problem) is not a key-health issue
— it will fail identically on every key — so it is raised immediately
without burning the rest of the pool's quota on a doomed retry.

Note: rotation only adds real headroom if each key belongs to a
different Google Cloud project/billing account. Keys sharing one
project share one quota; rotating among them just spreads the same
zero-sum budget around faster.
"""

from __future__ import annotations

import json
import time
from typing import Any

from app.providers.llm.base import LLMProvider

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
        """Per-key health metrics (docs/work.md B2). Only the last 4
        characters of each key are ever included — safe to log or expose
        on an internal debug endpoint."""
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
            else:
                slot.success_count += 1
                return json.loads(response.text)

        if last_exc is not None:
            raise last_exc
        raise RuntimeError("All Gemini API keys are cooling down; no healthy key available")
