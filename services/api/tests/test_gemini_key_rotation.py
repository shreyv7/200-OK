"""Key-pool rotation/cooldown behavior for GeminiLLMProvider.
Uses a fake client so this stays fast and deterministic.
"""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest
from google.genai import errors

from app.providers.llm.base import LLMProviderUnavailable
from app.providers.llm.gemini import GeminiLLMProvider

_SCHEMA = {"type": "object", "properties": {"ok": {"type": "boolean"}}}
_MESSAGES = [{"role": "user", "content": "hi"}]


def _client_error(code: int, status: str) -> errors.ClientError:
    return errors.ClientError(code, {"error": {"message": status, "status": status}})


def _server_error(code: int, status: str) -> errors.ServerError:
    return errors.ServerError(code, {"error": {"message": status, "status": status}})


class _FakeResponse:
    def __init__(self, payload: dict, usage_metadata=None) -> None:
        self.text = json.dumps(payload)
        self.usage_metadata = usage_metadata


def _fake_client(sequence):
    class _Models:
        def generate_content(self, *, model, contents, config):
            outcome = sequence.pop(0)
            if isinstance(outcome, Exception):
                raise outcome
            return _FakeResponse(outcome)

    class _Client:
        def __init__(self) -> None:
            self.models = _Models()

    return _Client()


def test_round_robin_cycles_across_keys() -> None:
    provider = GeminiLLMProvider(api_keys=["key-a", "key-b"], model="gemini-2.5-flash-lite")
    seq_a = [{"ok": True}]
    seq_b = [{"ok": True}]

    def fake_builder(slot):
        return _fake_client(seq_a if slot.key == "key-a" else seq_b)

    with patch.object(provider, "_client_for", side_effect=fake_builder):
        res1 = provider.generate_structured(_SCHEMA, _MESSAGES)
        res2 = provider.generate_structured(_SCHEMA, _MESSAGES)
        assert res1 == {"ok": True}
        assert res2 == {"ok": True}


def test_429_cools_down_key_and_retries_next_slot() -> None:
    provider = GeminiLLMProvider(api_keys=["key-a", "key-b"], model="gemini-2.5-flash-lite")
    seq_a = [_client_error(429, "RESOURCE_EXHAUSTED")]
    seq_b = [{"ok": True}]

    def fake_builder(slot):
        return _fake_client(seq_a if slot.key == "key-a" else seq_b)

    with patch.object(provider, "_client_for", side_effect=fake_builder):
        res = provider.generate_structured(_SCHEMA, _MESSAGES)
        assert res == {"ok": True}

    health = provider.key_health()
    assert health[0]["cooling_down"] is True
    assert health[1]["cooling_down"] is False


def test_exhausted_pool_raises_llm_provider_unavailable() -> None:
    provider = GeminiLLMProvider(api_keys=["key-a"], model="gemini-2.5-flash-lite")
    seq_a = [_client_error(429, "RESOURCE_EXHAUSTED")]

    def fake_builder(slot):
        return _fake_client(seq_a)

    with patch.object(provider, "_client_for", side_effect=fake_builder):
        with pytest.raises(LLMProviderUnavailable):
            provider.generate_structured(_SCHEMA, _MESSAGES)
