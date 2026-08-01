from __future__ import annotations

import pytest

from app.core.config import Settings
from app.core.di import get_search_provider
from app.providers.search.fake import FakeSearchProvider


def test_default_settings_resolve_to_fake_search_provider() -> None:
    settings = Settings(_env_file=None, search_provider="fake")
    provider = get_search_provider(settings)
    assert isinstance(provider, FakeSearchProvider)




def test_tavily_without_api_key_raises() -> None:
    settings = Settings(search_provider="tavily", tavily_api_key=None)
    with pytest.raises(RuntimeError):
        get_search_provider(settings)
