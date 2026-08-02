"""Per-user daily LLM call cap + token usage logging. Owner: Backend.
docs/work.md B5.

Wraps another LLMProvider (typically the outermost one — Gemini alone,
or FailoverLLMProvider — so the cap applies regardless of which vendor
ends up serving the request, since both cost money). Must be constructed
per-request: it needs a live db Session and the authenticated user_id,
see app/core/di.py get_budgeted_llm_provider().
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.providers.llm.base import LLMProvider


class LLMBudgetExceeded(RuntimeError):
    """Raised when a user has hit their daily LLM call cap.

    Deliberately NOT a subclass of LLMProviderUnavailable: a budget cap
    is a deliberate policy decision, not a transient provider failure.
    If it were LLMProviderUnavailable, FailoverLLMProvider would catch it
    and silently spend Bedrock quota routing around a user's own Gemini
    cap — defeating the entire point of a cost guardrail."""


class BudgetedLLMProvider(LLMProvider):
    def __init__(self, inner: LLMProvider, db: Session, user_id: str, daily_call_cap: int) -> None:
        self._inner = inner
        self._db = db
        self._user_id = user_id
        self._daily_call_cap = daily_call_cap

    def generate_structured(
        self,
        schema: dict[str, Any],
        messages: list[dict[str, str]],
        opts: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        from app.repositories import llm_usage_repository

        budget = llm_usage_repository.get_or_create(self._db, self._user_id)
        if budget.calls_today >= self._daily_call_cap:
            raise LLMBudgetExceeded(
                f"User {self._user_id} has reached today's LLM call cap ({self._daily_call_cap})"
            )

        result = self._inner.generate_structured(schema, messages, opts)

        usage = self._inner.last_usage
        llm_usage_repository.record_call(
            self._db,
            self._user_id,
            total_tokens=(usage.total_tokens if usage and usage.total_tokens else 0),
        )
        return result

    def generate_structured_from_image(
        self,
        schema: dict[str, Any],
        prompt: str,
        image_bytes: bytes,
        mime_type: str = "image/png",
        opts: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        from app.repositories import llm_usage_repository

        budget = llm_usage_repository.get_or_create(self._db, self._user_id)
        if budget.calls_today >= self._daily_call_cap:
            raise LLMBudgetExceeded(
                f"User {self._user_id} has reached today's LLM call cap ({self._daily_call_cap})"
            )

        result = self._inner.generate_structured_from_image(
            schema, prompt, image_bytes, mime_type, opts
        )

        usage = self._inner.last_usage
        llm_usage_repository.record_call(
            self._db,
            self._user_id,
            total_tokens=(usage.total_tokens if usage and usage.total_tokens else 0),
        )
        return result
