from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

from app.core.config import Settings
from app.core.di import get_search_provider
from app.providers.search.base import Document
from app.providers.search.fake import FakeSearchProvider
from app.providers.search.tavily import TavilySearchProvider


def _mock_tavily_client(fake_response: object) -> MagicMock:
    mock_module = MagicMock()
    mock_instance = MagicMock()
    mock_instance.search.return_value = fake_response
    mock_module.TavilyClient.return_value = mock_instance
    return mock_module


def test_tavily_search_success_mapping() -> None:
    fake_response = {
        "results": [
            {
                "title": "Deep Work Habits",
                "url": "https://example.com/deep-work",
                "content": "A summary of deep work principles.",
                "score": 0.95,
            },
            {
                "title": "Focus Techniques",
                "url": "https://example.com/focus",
                "content": "Strategies for eliminating digital distractions.",
                "score": 0.88,
            },
        ]
    }

    mock_module = _mock_tavily_client(fake_response)
    with patch.dict(sys.modules, {"tavily": mock_module}):
        provider = TavilySearchProvider(api_key="tvly-test-key", timeout_seconds=1.5)
        docs = provider.search("how to build focus")

        assert len(docs) == 2
        assert docs[0].title == "Deep Work Habits"
        assert docs[0].url == "https://example.com/deep-work"
        assert docs[0].extract == "A summary of deep work principles."
        assert docs[0].source in {"tavily", "tavily_live"}

        mock_module.TavilyClient.return_value.search.assert_called_once_with(
            "how to build focus", timeout=1.5
        )


def test_tavily_filters_invalid_results() -> None:
    fake_response = {
        "results": [
            {"title": "", "url": "https://example.com/empty-title", "content": "valid content"},
            {"title": "No URL", "url": "", "content": "valid content"},
            {"title": "No Content", "url": "https://example.com/no-content", "content": ""},
            {"title": "Valid Item", "url": "https://example.com/valid", "content": "Good summary"},
            "not a dict item",
        ]
    }

    mock_module = _mock_tavily_client(fake_response)
    with patch.dict(sys.modules, {"tavily": mock_module}):
        provider = TavilySearchProvider(api_key="tvly-test-key")
        docs = provider.search("invalid fields test")

        assert len(docs) == 1
        assert docs[0].title == "Valid Item"


def test_tavily_handles_non_dict_response() -> None:
    mock_module = _mock_tavily_client("invalid non-dict response")
    with patch.dict(sys.modules, {"tavily": mock_module}):
        provider = TavilySearchProvider(api_key="tvly-test-key")
        docs = provider.search("non dict test")

        # Never raise / never empty — curated web cards keep the feed alive.
        assert len(docs) >= 1
        assert all(d.source == "curated_web_fallback" for d in docs)


def test_get_search_provider_di_tavily() -> None:
    settings = Settings(
        _env_file=None,
        search_provider="tavily",
        tavily_api_key="tvly-real-key-123",
        tavily_timeout_seconds=2.0,
    )
    mock_module = _mock_tavily_client({"results": []})
    with patch.dict(sys.modules, {"tavily": mock_module}):
        provider = get_search_provider(settings)
        assert isinstance(provider, TavilySearchProvider)
        assert provider._timeout_seconds == 2.0


def test_get_search_provider_di_fake() -> None:
    settings = Settings(_env_file=None, search_provider="fake")
    provider = get_search_provider(settings)
    assert isinstance(provider, FakeSearchProvider)
