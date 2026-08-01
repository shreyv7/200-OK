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
"""

from __future__ import annotations

import json
from typing import Any

from app.providers.llm.base import LLMProvider


class GeminiLLMProvider(LLMProvider):
    """Single-key Gemini provider. Key rotation/pooling is out of B1 scope (docs/work.md B2)."""

    def __init__(self, api_key: str, model: str) -> None:
        from google import genai

        self._client = genai.Client(api_key=api_key)
        self._model = model

    def generate_structured(
        self,
        schema: dict[str, Any],
        messages: list[dict[str, str]],
        opts: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        from google.genai import types

        prompt = "\n\n".join(f"[{m['role']}] {m['content']}" for m in messages)
        response = self._client.models.generate_content(
            model=self._model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_json_schema=schema,
            ),
        )
        return json.loads(response.text)
