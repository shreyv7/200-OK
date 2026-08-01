"""Provider-agnostic LLM failover. Owner: Backend. docs/work.md B3.

Wraps a primary LLMProvider with a fallback; on LLMProviderUnavailable
from the primary (rate limit, quota exhaustion, outage — see
app/providers/llm/base.py), retries once against the fallback. Any other
exception (malformed request, programming error) propagates immediately
without touching the fallback, since it will fail identically there.

Imports no vendor SDK — this file only knows about the LLMProvider
interface, matching techstack §11.1's "no feature imports Gemini/
Bedrock/Tavily SDKs outside providers/" (the concrete providers it wraps
are the ones allowed to do that, each in its own file).
"""

from __future__ import annotations

from typing import Any

from app.providers.llm.base import LLMProvider, LLMProviderUnavailable


class FailoverLLMProvider(LLMProvider):
    def __init__(self, primary: LLMProvider, fallback: LLMProvider) -> None:
        self._primary = primary
        self._fallback = fallback

    def generate_structured(
        self,
        schema: dict[str, Any],
        messages: list[dict[str, str]],
        opts: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        try:
            return self._primary.generate_structured(schema, messages, opts)
        except LLMProviderUnavailable:
            return self._fallback.generate_structured(schema, messages, opts)
