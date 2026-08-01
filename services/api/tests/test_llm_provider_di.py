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
    settings = Settings(llm_provider="gemini", gemini_api_key=None)
    with pytest.raises(RuntimeError):
        get_llm_provider(settings)


def test_bedrock_resolves_to_stub_provider() -> None:
    settings = Settings(llm_provider="bedrock")
    provider = get_llm_provider(settings)
    assert isinstance(provider, BedrockLLMProvider)
    with pytest.raises(NotImplementedError):
        provider.generate_structured(schema={}, messages=[])
