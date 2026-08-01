"""B2 (docs/work.md): key-pool rotation/cooldown behavior for
GeminiLLMProvider. Uses a fake client (no real google.genai network call,
no live key needed) so this stays fast and deterministic like the rest
of the suite — see docs/work.md ground rule 5."""

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
    def __init__(self, payload: dict) -> None:
        self.text = json.dumps(payload)


def _fake_client(sequence):
    """Returns an object shaped like google.genai.Client whose
    .models.generate_content() pops the next item from `sequence`
    (either an exception instance to raise, or a dict payload to
    succeed with)."""

    class _Models:
        def generate_content(self, *, model, contents, config):
            outcome = sequence.pop(0)
            if isinstance(outcome, Exception):
                raise outcome
            return _FakeResponse(outcome)

    class _Client:
        models = _Models()

    return _Client()


def test_single_healthy_key_succeeds() -> None:
    provider = GeminiLLMProvider(api_keys=["key-a"], model="gemini-2.0-flash")
    with patch("google.genai.Client", return_value=_fake_client([{"ok": True}])):
        result = provider.generate_structured(schema=_SCHEMA, messages=_MESSAGES)
    assert result == {"ok": True}
    health = provider.key_health()
    assert health[0]["success_count"] == 1
    assert health[0]["failure_count"] == 0


def test_rotates_to_next_key_on_rate_limit() -> None:
    provider = GeminiLLMProvider(api_keys=["key-a", "key-b"], model="gemini-2.0-flash")
    clients = {
        "key-a": _fake_client([_client_error(429, "RESOURCE_EXHAUSTED")]),
        "key-b": _fake_client([{"ok": True}]),
    }

    def fake_genai_client(*, api_key):
        return clients[api_key]

    with patch("google.genai.Client", side_effect=fake_genai_client):
        result = provider.generate_structured(schema=_SCHEMA, messages=_MESSAGES)

    assert result == {"ok": True}
    health = {h["key_suffix"]: h for h in provider.key_health()}
    # key suffixes are the last 4 chars of "key-a"/"key-b" -- distinct enough here
    assert any(h["failure_count"] == 1 and h["cooling_down"] for h in health.values())
    assert any(h["success_count"] == 1 for h in health.values())


def test_rotates_to_next_key_on_server_error() -> None:
    provider = GeminiLLMProvider(api_keys=["key-a", "key-b"], model="gemini-2.0-flash")
    clients = {
        "key-a": _fake_client([_server_error(503, "UNAVAILABLE")]),
        "key-b": _fake_client([{"ok": True}]),
    }
    with patch("google.genai.Client", side_effect=lambda *, api_key: clients[api_key]):
        result = provider.generate_structured(schema=_SCHEMA, messages=_MESSAGES)
    assert result == {"ok": True}


def test_all_keys_cooling_down_raises_last_error() -> None:
    """Raises the provider-agnostic LLMProviderUnavailable (docs/work.md
    B3), not a raw google.genai exception, so FailoverLLMProvider can
    catch one generic type without importing google.genai.errors."""
    provider = GeminiLLMProvider(api_keys=["key-a", "key-b"], model="gemini-2.0-flash")
    clients = {
        "key-a": _fake_client([_client_error(429, "RESOURCE_EXHAUSTED")]),
        "key-b": _fake_client([_client_error(429, "RESOURCE_EXHAUSTED")]),
    }
    with patch("google.genai.Client", side_effect=lambda *, api_key: clients[api_key]):
        with pytest.raises(LLMProviderUnavailable):
            provider.generate_structured(schema=_SCHEMA, messages=_MESSAGES)

    # Second call: both keys are now in cooldown, no client should even be
    # constructed again -- proves it fails fast without wasting a real call.
    with patch("google.genai.Client", side_effect=AssertionError("should not build a client")):
        with pytest.raises(LLMProviderUnavailable, match="cooling down"):
            provider.generate_structured(schema=_SCHEMA, messages=_MESSAGES)


def test_invalid_key_error_does_not_retry_immediately_on_same_key() -> None:
    provider = GeminiLLMProvider(api_keys=["key-a", "key-b"], model="gemini-2.0-flash")
    clients = {
        "key-a": _fake_client([_client_error(401, "UNAUTHENTICATED")]),
        "key-b": _fake_client([{"ok": True}]),
    }
    with patch("google.genai.Client", side_effect=lambda *, api_key: clients[api_key]):
        result = provider.generate_structured(schema=_SCHEMA, messages=_MESSAGES)
    assert result == {"ok": True}
    health = {h["key_suffix"]: h for h in provider.key_health()}
    assert any(h["cooling_down"] and h["failure_count"] == 1 for h in health.values())


def test_malformed_request_error_raises_without_trying_other_keys() -> None:
    """A 400 (e.g. bad schema) is not a key-health problem -- it will fail
    identically on every key, so the provider must not burn the rest of
    the pool's quota retrying it."""
    provider = GeminiLLMProvider(api_keys=["key-a", "key-b"], model="gemini-2.0-flash")
    second_client_built = False

    def fake_genai_client(*, api_key):
        nonlocal second_client_built
        if api_key == "key-a":
            return _fake_client([_client_error(400, "INVALID_ARGUMENT")])
        second_client_built = True
        raise AssertionError("should not have tried the second key")

    with patch("google.genai.Client", side_effect=fake_genai_client):
        with pytest.raises(errors.ClientError):
            provider.generate_structured(schema=_SCHEMA, messages=_MESSAGES)

    assert second_client_built is False


def test_key_health_never_exposes_full_key() -> None:
    provider = GeminiLLMProvider(api_keys=["AIzaSyABCDEFGHIJKLMNOPQRSTUVWXYZ12345"], model="m")
    health = provider.key_health()
    assert health[0]["key_suffix"] == "2345"
    assert "AIzaSy" not in json.dumps(health)


def test_round_robin_rotates_starting_key_across_calls() -> None:
    provider = GeminiLLMProvider(api_keys=["key-a", "key-b"], model="gemini-2.0-flash")
    calls_by_key: dict[str, int] = {"key-a": 0, "key-b": 0}

    def fake_genai_client(*, api_key):
        def make():
            def generate_content(*, model, contents, config):
                calls_by_key[api_key] += 1
                return _FakeResponse({"ok": True})

            client = type("C", (), {})()
            client.models = type("M", (), {"generate_content": staticmethod(generate_content)})()
            return client

        return make()

    with patch("google.genai.Client", side_effect=fake_genai_client):
        provider.generate_structured(schema=_SCHEMA, messages=_MESSAGES)
        provider.generate_structured(schema=_SCHEMA, messages=_MESSAGES)

    # First call starts at key-a, second call starts at key-b -- both get used.
    assert calls_by_key["key-a"] == 1
    assert calls_by_key["key-b"] == 1
