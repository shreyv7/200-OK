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
    # gemini_api_keys="" is pinned explicitly, not left to ambient env/.env —
    # otherwise a developer's local .env (real keys, gitignored) leaks into
    # Settings() for any field this test doesn't set, silently making an
    # "empty pool" test pass with a non-empty pool.
    settings = Settings(llm_provider="gemini", gemini_api_key=None, gemini_api_keys="")
    with pytest.raises(RuntimeError):
        get_llm_provider(settings)


def test_gemini_with_api_key_resolves_real_provider() -> None:
    """B1 (docs/work.md): proves LLM_PROVIDER=gemini actually wires up the
    real Gemini SDK client rather than silently falling back to the fake.
    Uses a placeholder key — genai.Client(...) is local SDK object
    construction, no network call happens until generate_content()."""
    from app.providers.llm.gemini import GeminiLLMProvider

    settings = Settings(
        llm_provider="gemini", gemini_api_key="test-placeholder-key", gemini_model="gemini-2.0-flash"
    )
    provider = get_llm_provider(settings)
    assert isinstance(provider, GeminiLLMProvider)


def test_gemini_api_key_pool_combines_and_dedupes() -> None:
    """B2 (docs/work.md): GEMINI_API_KEY and GEMINI_API_KEYS combine into
    one ordered, de-duplicated rotation pool."""
    settings = Settings(
        gemini_api_key="key-a", gemini_api_keys=" key-b , key-a ,key-c,,key-b "
    )
    assert settings.gemini_api_key_pool() == ["key-a", "key-b", "key-c"]


def test_gemini_with_key_pool_resolves_provider_with_all_slots() -> None:
    from app.providers.llm.gemini import GeminiLLMProvider

    settings = Settings(
        llm_provider="gemini",
        gemini_api_key="key-a",
        gemini_api_keys="key-b,key-c",
        gemini_model="gemini-2.0-flash",
    )
    provider = get_llm_provider(settings)
    assert isinstance(provider, GeminiLLMProvider)
    assert len(provider.key_health()) == 3


def test_gemini_config_accepts_nested_pydantic_schema() -> None:
    """Regression test for a real bug found live against Gemini while
    wiring B1: google.generativeai's response_schema is a flattened
    OpenAPI-subset proto that raises `ValueError: Unknown field for
    Schema: $defs` for ANY schema with a nested model — client-side,
    before any network call — which broke every structured LLM call in
    this codebase (onboarding extraction, bottleneck diagnosis, weekly
    report, evolution proposals all nest models). google.genai's
    response_json_schema field explicitly supports $defs/$ref instead.
    This proves the schema our own onboarding extraction actually sends
    (attributes -> markers, i.e. real $defs/$ref) builds a valid request
    config without that exception — the failure mode this test guards
    against needs no network call to reproduce, so this stays a fast
    offline unit test."""
    from google.genai import types

    from app.services.identity.onboarding_orchestration import _ExtractionSchema

    schema = _ExtractionSchema.model_json_schema()
    assert "$defs" in schema  # sanity: this schema is genuinely nested

    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_json_schema=schema,
    )
    assert config.response_json_schema is not None
    assert "$defs" in config.response_json_schema


def test_bedrock_without_config_raises_at_construction() -> None:
    """B3 (docs/work.md): Bedrock is a real provider now, not an inert
    stub -- missing region/model config fails fast at construction, not
    silently on first call."""
    settings = Settings(llm_provider="bedrock", bedrock_region=None, bedrock_model_id=None)
    with pytest.raises(RuntimeError):
        get_llm_provider(settings)


def test_bedrock_with_config_resolves_real_provider() -> None:
    settings = Settings(
        llm_provider="bedrock", bedrock_region="us-east-1", bedrock_model_id="test-model"
    )
    provider = get_llm_provider(settings)
    assert isinstance(provider, BedrockLLMProvider)


def test_gemini_without_bedrock_failover_flag_stays_plain_gemini() -> None:
    """Off by default (docs/work.md B3 ground rule) -- even with Bedrock
    fully configured, LLM_PROVIDER=gemini alone must not wrap in failover
    unless BEDROCK_FAILOVER_ENABLED=true is also set."""
    from app.providers.llm.gemini import GeminiLLMProvider

    settings = Settings(
        llm_provider="gemini",
        gemini_api_key="key-a",
        bedrock_failover_enabled=False,
        bedrock_region="us-east-1",
        bedrock_model_id="test-model",
    )
    provider = get_llm_provider(settings)
    assert isinstance(provider, GeminiLLMProvider)


def test_gemini_with_bedrock_failover_flag_wraps_in_failover_provider() -> None:
    from app.providers.llm.failover import FailoverLLMProvider

    settings = Settings(
        llm_provider="gemini",
        gemini_api_key="key-a",
        bedrock_failover_enabled=True,
        bedrock_region="us-east-1",
        bedrock_model_id="test-model",
    )
    provider = get_llm_provider(settings)
    assert isinstance(provider, FailoverLLMProvider)


def test_gemini_with_bedrock_failover_flag_but_missing_bedrock_config_stays_plain_gemini() -> None:
    """The flag alone isn't enough -- region/model_id must also be set,
    otherwise BedrockLLMProvider's own construction would raise and take
    the whole app down for a misconfigured opt-in feature."""
    from app.providers.llm.gemini import GeminiLLMProvider

    settings = Settings(
        llm_provider="gemini",
        gemini_api_key="key-a",
        bedrock_failover_enabled=True,
        bedrock_region=None,
        bedrock_model_id=None,
    )
    provider = get_llm_provider(settings)
    assert isinstance(provider, GeminiLLMProvider)
