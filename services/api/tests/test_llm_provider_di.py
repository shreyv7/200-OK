from __future__ import annotations

import pytest

from app.core.config import Settings
from app.core.di import get_llm_provider
from app.providers.llm.bedrock import BedrockLLMProvider
from app.providers.llm.fake import FakeLLMProvider


def test_default_settings_resolve_to_fake_provider() -> None:
    settings = Settings(llm_provider="fake")
    provider = get_llm_provider(settings)
    assert isinstance(provider, FakeLLMProvider)


def test_gemini_without_api_key_raises() -> None:
    settings = Settings(llm_provider="gemini", gemini_api_key=None, gemini_api_keys="")
    with pytest.raises(RuntimeError):
        get_llm_provider(settings)


def test_gemini_with_api_key_resolves_real_provider() -> None:
    """B1 (docs/work.md): proves LLM_PROVIDER=gemini actually wires up the
    real Gemini SDK client rather than silently falling back to the fake."""
    from app.providers.llm.gemini import GeminiLLMProvider

    settings = Settings(
        llm_provider="gemini", gemini_api_key="test-placeholder-key", gemini_model="gemini-2.5-flash-lite"
    )
    provider = get_llm_provider(settings)
    assert isinstance(provider, GeminiLLMProvider)


def test_gemini_api_key_pool_combines_and_dedupes() -> None:
    """B2 (docs/work.md): GEMINI_API_KEY and GEMINI_API_KEYS combine into
    one ordered, de-duplicated rotation pool."""
    settings = Settings(
        gemini_api_key="key-a, key-d", gemini_api_keys=" key-b , key-a ,key-c,,key-b "
    )
    assert settings.gemini_api_key_pool() == ["key-a", "key-d", "key-b", "key-c"]


def test_gemini_with_key_pool_resolves_provider_with_all_slots() -> None:
    from app.providers.llm.gemini import GeminiLLMProvider

    settings = Settings(
        llm_provider="gemini",
        gemini_api_key="key-a",
        gemini_api_keys="key-b,key-c",
        gemini_model="gemini-2.5-flash-lite",
    )
    provider = get_llm_provider(settings)
    assert isinstance(provider, GeminiLLMProvider)
    assert len(provider.key_health()) == 3


def test_gemini_config_accepts_nested_pydantic_schema() -> None:
    """Proves nested schema support in google.genai GenerateContentConfig."""
    from google.genai import types
    from pydantic import BaseModel

    class InnerModel(BaseModel):
        val: str

    class OuterModel(BaseModel):
        inner: InnerModel

    schema = OuterModel.model_json_schema()
    assert "$defs" in schema

    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_json_schema=schema,
    )
    assert config.response_json_schema is not None
    assert "$defs" in config.response_json_schema


def test_bedrock_with_config_resolves_real_provider() -> None:
    settings = Settings(
        llm_provider="bedrock", bedrock_region="us-east-1", bedrock_model_id="test-model"
    )
    provider = get_llm_provider(settings)
    assert isinstance(provider, BedrockLLMProvider)
