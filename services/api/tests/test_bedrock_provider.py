"""B3 (docs/work.md): BedrockLLMProvider structured-output call shape.
Mocks boto3 entirely -- no live AWS account needed (ground rule 5: fakes
stay the default for tests). This is a stub test per the B3 ground rule
("if we don't buy Bedrock yet, ship the failover code behind a flag with
a stub test") -- it proves the call is built and parsed correctly, not
that a real AWS account accepts it."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from app.providers.llm.base import LLMProviderUnavailable
from app.providers.llm.bedrock import BedrockLLMProvider

_SCHEMA = {"type": "object", "properties": {"ok": {"type": "boolean"}}}


def _tool_use_response(payload: dict) -> dict:
    return {
        "output": {
            "message": {
                "content": [{"toolUse": {"name": "emit_structured_output", "input": payload}}]
            }
        },
        "stopReason": "tool_use",
    }


def _client_error(code: str) -> ClientError:
    return ClientError({"Error": {"Code": code, "Message": code}}, "Converse")


def test_missing_region_or_model_raises_at_construction() -> None:
    with pytest.raises(RuntimeError):
        BedrockLLMProvider(region=None, model_id="m")
    with pytest.raises(RuntimeError):
        BedrockLLMProvider(region="us-east-1", model_id=None)


def test_generate_structured_returns_tool_use_input() -> None:
    provider = BedrockLLMProvider(region="us-east-1", model_id="test-model")
    fake_client = MagicMock()
    fake_client.converse.return_value = _tool_use_response({"ok": True})

    with patch("boto3.client", return_value=fake_client):
        result = provider.generate_structured(
            schema=_SCHEMA, messages=[{"role": "user", "content": "hi"}]
        )

    assert result == {"ok": True}
    call_kwargs = fake_client.converse.call_args.kwargs
    assert call_kwargs["modelId"] == "test-model"
    assert call_kwargs["toolConfig"]["toolChoice"] == {"tool": {"name": "emit_structured_output"}}
    assert call_kwargs["toolConfig"]["tools"][0]["toolSpec"]["inputSchema"]["json"] == _SCHEMA


def test_system_messages_go_in_system_field_not_messages() -> None:
    provider = BedrockLLMProvider(region="us-east-1", model_id="test-model")
    fake_client = MagicMock()
    fake_client.converse.return_value = _tool_use_response({"ok": True})

    with patch("boto3.client", return_value=fake_client):
        provider.generate_structured(
            schema=_SCHEMA,
            messages=[
                {"role": "system", "content": "You are helpful."},
                {"role": "user", "content": "hi"},
            ],
        )

    call_kwargs = fake_client.converse.call_args.kwargs
    assert call_kwargs["system"] == [{"text": "You are helpful."}]
    assert call_kwargs["messages"] == [{"role": "user", "content": [{"text": "hi"}]}]


def test_no_system_messages_omits_system_field() -> None:
    provider = BedrockLLMProvider(region="us-east-1", model_id="test-model")
    fake_client = MagicMock()
    fake_client.converse.return_value = _tool_use_response({"ok": True})

    with patch("boto3.client", return_value=fake_client):
        provider.generate_structured(schema=_SCHEMA, messages=[{"role": "user", "content": "hi"}])

    assert "system" not in fake_client.converse.call_args.kwargs


def test_retryable_client_error_raises_llm_provider_unavailable() -> None:
    provider = BedrockLLMProvider(region="us-east-1", model_id="test-model")
    fake_client = MagicMock()
    fake_client.converse.side_effect = _client_error("ThrottlingException")

    with patch("boto3.client", return_value=fake_client):
        with pytest.raises(LLMProviderUnavailable):
            provider.generate_structured(schema=_SCHEMA, messages=[{"role": "user", "content": "hi"}])


def test_non_retryable_client_error_propagates_unwrapped() -> None:
    provider = BedrockLLMProvider(region="us-east-1", model_id="test-model")
    fake_client = MagicMock()
    fake_client.converse.side_effect = _client_error("ValidationException")

    with patch("boto3.client", return_value=fake_client):
        with pytest.raises(ClientError):
            provider.generate_structured(schema=_SCHEMA, messages=[{"role": "user", "content": "hi"}])


def test_missing_tool_use_block_raises_llm_provider_unavailable() -> None:
    provider = BedrockLLMProvider(region="us-east-1", model_id="test-model")
    fake_client = MagicMock()
    fake_client.converse.return_value = {
        "output": {"message": {"content": [{"text": "I refuse to call the tool."}]}},
        "stopReason": "end_turn",
    }

    with patch("boto3.client", return_value=fake_client):
        with pytest.raises(LLMProviderUnavailable):
            provider.generate_structured(schema=_SCHEMA, messages=[{"role": "user", "content": "hi"}])
