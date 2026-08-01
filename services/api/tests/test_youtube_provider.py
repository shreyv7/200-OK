from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.core.config import Settings
from app.core.di import get_youtube_provider
from app.providers.search.youtube import YouTubeMediaProvider


def test_youtube_search_success_mapping() -> None:
    fake_api_response = {
        "items": [
            {
                "id": {"videoId": "gT8g001zJwc"},
                "snippet": {
                    "title": "Deep Work - How to Focus",
                    "description": "Strategies for intense concentration.",
                    "channelTitle": "Productivity Hub",
                    "thumbnails": {"high": {"url": "https://img.youtube.com/vi/gT8g001zJwc/high.jpg"}},
                },
            },
            {
                "id": {"videoId": "abc123xyz"},
                "snippet": {
                    "title": "Atomic Habits Masterclass",
                    "description": "Tiny changes, remarkable results.",
                    "channelTitle": "Growth Daily",
                    "thumbnails": {"medium": {"url": "https://img.youtube.com/vi/abc123xyz/med.jpg"}},
                },
            },
        ]
    }

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = fake_api_response

    with patch("httpx.Client") as MockClient:
        mock_client_instance = MagicMock()
        mock_client_instance.get.return_value = mock_response
        MockClient.return_value.__enter__.return_value = mock_client_instance

        provider = YouTubeMediaProvider(api_key="AIzaSyTestKey123", timeout_seconds=2.0)
        docs = provider.search("deep work tutorial")

        assert len(docs) == 2
        assert docs[0].title == "Deep Work - How to Focus"
        assert docs[0].url == "https://www.youtube.com/watch?v=gT8g001zJwc"
        assert docs[0].extract == "Strategies for intense concentration."
        assert docs[0].source == "youtube"
        assert docs[0].metadata["video_id"] == "gT8g001zJwc"
        assert docs[0].metadata["channel_title"] == "Productivity Hub"
        assert docs[0].metadata["thumbnail_url"] == "https://img.youtube.com/vi/gT8g001zJwc/high.jpg"


def test_youtube_missing_api_key_returns_fallback() -> None:
    provider = YouTubeMediaProvider(api_key=None)
    docs = provider.search("any query")

    assert len(docs) >= 1
    assert docs[0].source == "curated_youtube_fallback"
    assert "youtube.com" in docs[0].url


def test_youtube_http_error_returns_fallback() -> None:
    mock_response = MagicMock()
    mock_response.status_code = 403

    with patch("httpx.Client") as MockClient:
        mock_client_instance = MagicMock()
        mock_client_instance.get.return_value = mock_response
        MockClient.return_value.__enter__.return_value = mock_client_instance

        provider = YouTubeMediaProvider(api_key="AIzaSyInvalidKey")
        docs = provider.search("query on 403 error")

        assert len(docs) >= 1
        assert docs[0].source == "curated_youtube_fallback"


def test_youtube_network_exception_returns_fallback() -> None:
    with patch("httpx.Client") as MockClient:
        mock_client_instance = MagicMock()
        mock_client_instance.get.side_effect = RuntimeError("Network timeout")
        MockClient.return_value.__enter__.return_value = mock_client_instance

        provider = YouTubeMediaProvider(api_key="AIzaSyKey")
        docs = provider.search("query on timeout exception")

        assert len(docs) >= 1
        assert docs[0].source == "curated_youtube_fallback"


def test_get_youtube_provider_di() -> None:
    settings = Settings(youtube_api_key="AIzaSyConfigKey", youtube_timeout_seconds=2.5)
    provider = get_youtube_provider(settings)

    assert isinstance(provider, YouTubeMediaProvider)
    assert provider._api_key == "AIzaSyConfigKey"
    assert provider._timeout_seconds == 2.5


def test_youtube_key_rotation_on_quota_error() -> None:
    res_quota_403 = MagicMock()
    res_quota_403.status_code = 403

    res_success_200 = MagicMock()
    res_success_200.status_code = 200
    res_success_200.json.return_value = {
        "items": [
            {
                "id": {"videoId": "rot123"},
                "snippet": {"title": "Rotation Video Success", "description": "Success after rotation"},
            }
        ]
    }

    with patch("httpx.Client") as MockClient:
        mock_client_instance = MagicMock()
        mock_client_instance.get.side_effect = [res_quota_403, res_success_200]
        MockClient.return_value.__enter__.return_value = mock_client_instance

        keys = ["AIzaSyPrimaryFail", "AIzaSyBackupSuccess"]
        provider = YouTubeMediaProvider(api_key=keys)
        docs = provider.search("testing rotation")

        assert len(docs) == 1
        assert docs[0].title == "Rotation Video Success"
        assert docs[0].metadata["video_id"] == "rot123"

