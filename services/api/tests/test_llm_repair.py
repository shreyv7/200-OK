"""B4 (docs/work.md): generate_structured_with_repair() behavior."""

from __future__ import annotations

import pytest

from app.providers.llm.base import LLMProvider, LLMProviderUnavailable
from app.providers.llm.repair import generate_structured_with_repair


class _SequenceProvider(LLMProvider):
    """Returns each item from `outcomes` in order; a dict succeeds, an
    Exception instance is raised."""

    def __init__(self, outcomes: list) -> None:
        self.outcomes = list(outcomes)
        self.calls: list[list[dict]] = []

    def generate_structured(self, schema, messages, opts=None):
        self.calls.append(messages)
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def _require_ok_key(raw):
    if not isinstance(raw, dict) or "ok" not in raw:
        raise ValueError("missing 'ok' key")
    return raw


def test_valid_first_response_returns_without_retry() -> None:
    provider = _SequenceProvider([{"ok": True}])
    result = generate_structured_with_repair(
        provider, schema={}, messages=[{"role": "user", "content": "hi"}], validate=_require_ok_key
    )
    assert result == {"ok": True}
    assert len(provider.calls) == 1


def test_invalid_first_response_retries_once_with_corrective_message() -> None:
    provider = _SequenceProvider([{"wrong": "shape"}, {"ok": True}])
    result = generate_structured_with_repair(
        provider, schema={}, messages=[{"role": "user", "content": "hi"}], validate=_require_ok_key
    )
    assert result == {"ok": True}
    assert len(provider.calls) == 2
    # second call appended a corrective follow-up on top of the original messages
    assert provider.calls[1][:1] == provider.calls[0]
    assert "invalid" in provider.calls[1][-1]["content"].lower()


def test_second_invalid_response_raises() -> None:
    provider = _SequenceProvider([{"wrong": "shape"}, {"still": "wrong"}])
    with pytest.raises(ValueError, match="missing 'ok' key"):
        generate_structured_with_repair(
            provider, schema={}, messages=[{"role": "user", "content": "hi"}], validate=_require_ok_key
        )
    assert len(provider.calls) == 2


def test_provider_unavailable_on_first_call_propagates_without_retry() -> None:
    """A transport-level failure (provider/pool already exhausted its own
    retries in B2/B3) should not trigger a repair retry -- that would just
    wait for the same guaranteed-transient failure again."""
    provider = _SequenceProvider([LLMProviderUnavailable("pool exhausted")])
    with pytest.raises(LLMProviderUnavailable):
        generate_structured_with_repair(
            provider, schema={}, messages=[{"role": "user", "content": "hi"}], validate=_require_ok_key
        )
    assert len(provider.calls) == 1


def test_provider_unavailable_on_retry_call_propagates() -> None:
    provider = _SequenceProvider([{"wrong": "shape"}, LLMProviderUnavailable("pool exhausted mid-repair")])
    with pytest.raises(LLMProviderUnavailable):
        generate_structured_with_repair(
            provider, schema={}, messages=[{"role": "user", "content": "hi"}], validate=_require_ok_key
        )
    assert len(provider.calls) == 2
