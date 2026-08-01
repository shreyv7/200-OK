"""B5 (docs/work.md): BudgetedLLMProvider cap enforcement + usage
recording."""

from __future__ import annotations

import pytest

from app.models.user import User
from app.providers.llm.base import LLMProvider, LLMUsage
from app.providers.llm.budget import BudgetedLLMProvider, LLMBudgetExceeded
from app.repositories import llm_usage_repository

_SCHEMA = {"type": "object"}
_MESSAGES = [{"role": "user", "content": "hi"}]


class _StubProvider(LLMProvider):
    def __init__(self, result: dict, usage: LLMUsage | None = None) -> None:
        self._result = result
        self.last_usage = usage
        self.calls = 0

    def generate_structured(self, schema, messages, opts=None):
        self.calls += 1
        return self._result


def _make_user(db_session, user_id: str) -> None:
    db_session.add(User(id=user_id, capacity=100.0))
    db_session.commit()


def test_call_under_cap_succeeds_and_records_usage(db_session) -> None:
    user_id = "user-budget-llm-1"
    _make_user(db_session, user_id)
    inner = _StubProvider({"ok": True}, usage=LLMUsage(total_tokens=42))
    provider = BudgetedLLMProvider(inner, db=db_session, user_id=user_id, daily_call_cap=5)

    result = provider.generate_structured(schema=_SCHEMA, messages=_MESSAGES)

    assert result == {"ok": True}
    assert inner.calls == 1
    row = llm_usage_repository.get_or_create(db_session, user_id)
    assert row.calls_today == 1
    assert row.tokens_today == 42


def test_call_at_cap_raises_without_calling_inner(db_session) -> None:
    user_id = "user-budget-llm-2"
    _make_user(db_session, user_id)
    inner = _StubProvider({"ok": True})
    provider = BudgetedLLMProvider(inner, db=db_session, user_id=user_id, daily_call_cap=2)

    provider.generate_structured(schema=_SCHEMA, messages=_MESSAGES)
    provider.generate_structured(schema=_SCHEMA, messages=_MESSAGES)
    assert inner.calls == 2

    with pytest.raises(LLMBudgetExceeded):
        provider.generate_structured(schema=_SCHEMA, messages=_MESSAGES)

    # the third (rejected) call must not have reached the inner provider
    assert inner.calls == 2


def test_missing_usage_records_zero_tokens(db_session) -> None:
    user_id = "user-budget-llm-3"
    _make_user(db_session, user_id)
    inner = _StubProvider({"ok": True}, usage=None)
    provider = BudgetedLLMProvider(inner, db=db_session, user_id=user_id, daily_call_cap=5)

    provider.generate_structured(schema=_SCHEMA, messages=_MESSAGES)

    row = llm_usage_repository.get_or_create(db_session, user_id)
    assert row.calls_today == 1
    assert row.tokens_today == 0


def test_budget_exceeded_is_not_llm_provider_unavailable() -> None:
    """Deliberately not a subclass — see budget.py's docstring: if it were,
    FailoverLLMProvider would catch it and silently spend Bedrock quota
    routing around a user's own cap."""
    from app.providers.llm.base import LLMProviderUnavailable

    assert not issubclass(LLMBudgetExceeded, LLMProviderUnavailable)
