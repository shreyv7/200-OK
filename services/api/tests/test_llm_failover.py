"""B3 (docs/work.md): FailoverLLMProvider behavior. Uses two fake
LLMProvider stand-ins -- no vendor SDK involved at all, so this is a
pure interface-level test."""

from __future__ import annotations

from typing import Any

import pytest

from app.providers.llm.base import LLMProvider, LLMProviderUnavailable
from app.providers.llm.failover import FailoverLLMProvider


class _StubProvider(LLMProvider):
    def __init__(self, outcome: Any) -> None:
        self.outcome = outcome
        self.calls = 0

    def generate_structured(self, schema, messages, opts=None):
        self.calls += 1
        if isinstance(self.outcome, Exception):
            raise self.outcome
        return self.outcome


def test_primary_success_never_touches_fallback() -> None:
    primary = _StubProvider({"from": "primary"})
    fallback = _StubProvider({"from": "fallback"})
    provider = FailoverLLMProvider(primary=primary, fallback=fallback)

    result = provider.generate_structured(schema={}, messages=[])

    assert result == {"from": "primary"}
    assert fallback.calls == 0


def test_provider_unavailable_falls_over_to_fallback() -> None:
    primary = _StubProvider(LLMProviderUnavailable("gemini pool exhausted"))
    fallback = _StubProvider({"from": "fallback"})
    provider = FailoverLLMProvider(primary=primary, fallback=fallback)

    result = provider.generate_structured(schema={}, messages=[])

    assert result == {"from": "fallback"}
    assert fallback.calls == 1


def test_other_exception_propagates_without_touching_fallback() -> None:
    """A malformed request (e.g. bad schema) is not availability -- it
    will fail identically on the fallback, so it must not be retried
    there and burn a Bedrock call for nothing."""
    primary = _StubProvider(ValueError("bad schema"))
    fallback = _StubProvider({"from": "fallback"})
    provider = FailoverLLMProvider(primary=primary, fallback=fallback)

    with pytest.raises(ValueError, match="bad schema"):
        provider.generate_structured(schema={}, messages=[])

    assert fallback.calls == 0
