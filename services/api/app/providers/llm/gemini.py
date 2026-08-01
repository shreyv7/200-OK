"""Real Google Gemini structured-output provider. Owner: Backend.

Only file in the repo allowed to import google.generativeai (hard
constraint, guidelines.md §9.3 / techstack.md §11.1). AIA/AIS call
`LLMProvider.generate_structured()` through DI — never this class
directly.
"""

from __future__ import annotations

import json
from typing import Any

from app.providers.llm.base import LLMProvider


class GeminiLLMProvider(LLMProvider):
    """Single-key Gemini provider. Key rotation/pooling is out of M3 scope."""

    def __init__(self, api_key: str, model: str) -> None:
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        self._model = genai.GenerativeModel(model)

    def generate_structured(
        self,
        schema: dict[str, Any],
        messages: list[dict[str, str]],
        opts: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        prompt = "\n\n".join(f"[{m['role']}] {m['content']}" for m in messages)
        response = self._model.generate_content(
            prompt,
            generation_config={
                "response_mime_type": "application/json",
                "response_schema": schema,
            },
        )
        return json.loads(response.text)
