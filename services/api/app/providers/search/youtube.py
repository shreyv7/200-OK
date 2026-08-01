"""YouTube Data API v3 media provider. Owner: Backend (work.md C2).

Fetches video metadata when a lens needs video/media content (e.g. Next Step /
knowledge lens). Falls back to curated media if API key is absent, rate-limited,
or timed out.
"""

from __future__ import annotations

from typing import Any

import httpx

from app.providers.search.base import Document, SearchProvider


_CURATED_YOUTUBE_FALLBACKS: list[Document] = [
    Document(
        title="Deep Work: Rules for Focused Success in a Distracted World",
        url="https://www.youtube.com/watch?v=gT8g001zJwc",
        extract="Key strategies for cultivating intense focus and eliminating digital friction.",
        source="curated_youtube_fallback",
        metadata={
            "video_id": "gT8g001zJwc",
            "channel_title": "Productivity Insights",
            "thumbnail_url": "https://img.youtube.com/vi/gT8g001zJwc/hqdefault.jpg",
        },
    ),
    Document(
        title="Building a Second Brain - Executive Summary",
        url="https://www.youtube.com/watch?v=K-ssA1x0000",
        extract="Methodology for capturing, organizing, and distilling personal knowledge.",
        source="curated_youtube_fallback",
        metadata={
            "video_id": "K-ssA1x0000",
            "channel_title": "Forte Labs",
            "thumbnail_url": "https://img.youtube.com/vi/K-ssA1x0000/hqdefault.jpg",
        },
    ),
]


class YouTubeMediaProvider(SearchProvider):
    def __init__(self, api_key: str | list[str] | None = None, timeout_seconds: float = 2.0) -> None:
        self._timeout_seconds = timeout_seconds
        self._endpoint = "https://www.googleapis.com/youtube/v3/search"
        if isinstance(api_key, list):
            self._api_keys = [k.strip() for k in api_key if k.strip()]
        elif isinstance(api_key, str) and api_key.strip():
            self._api_keys = [k.strip() for k in api_key.split(",") if k.strip()]
        else:
            self._api_keys = []

    @property
    def _api_key(self) -> str | None:
        return self._api_keys[0] if self._api_keys else None

    def search(self, query: str, opts: dict[str, Any] | None = None) -> list[Document]:

        if not self._api_keys:
            return self.get_fallback(query)

        max_results = opts.get("max_results", 5) if opts else 5

        for key in self._api_keys:
            params = {
                "part": "snippet",
                "type": "video",
                "q": query,
                "maxResults": max_results,
                "key": key,
            }

            try:
                with httpx.Client(timeout=self._timeout_seconds) as client:
                    res = client.get(self._endpoint, params=params)
                    if res.status_code != 200:
                        # Try next rotation key on 403 quota or 429 rate limit
                        continue
                    data = res.json()

                items = data.get("items", [])
                documents: list[Document] = []
                for item in items:
                    if not isinstance(item, dict):
                        continue
                    snippet = item.get("snippet", {})
                    id_data = item.get("id", {})
                    video_id = id_data.get("videoId") if isinstance(id_data, dict) else None
                    title = snippet.get("title") if isinstance(snippet, dict) else None
                    description = snippet.get("description") if isinstance(snippet, dict) else ""
                    channel_title = snippet.get("channelTitle", "") if isinstance(snippet, dict) else ""
                    thumbnails = snippet.get("thumbnails", {}) if isinstance(snippet, dict) else {}
                    thumbnail_url = ""
                    if isinstance(thumbnails, dict):
                        high = (
                            thumbnails.get("high", {})
                            or thumbnails.get("medium", {})
                            or thumbnails.get("default", {})
                        )
                        if isinstance(high, dict):
                            thumbnail_url = high.get("url", "")

                    if video_id and title:
                        documents.append(
                            Document(
                                title=str(title),
                                url=f"https://www.youtube.com/watch?v={video_id}",
                                extract=str(description or title),
                                source="youtube",
                                metadata={
                                    "video_id": str(video_id),
                                    "channel_title": str(channel_title),
                                    "thumbnail_url": str(thumbnail_url),
                                },
                            )
                        )
                if documents:
                    return documents

            except Exception:
                continue

        return self.get_fallback(query)


    def get_fallback(self, query: str) -> list[Document]:
        return list(_CURATED_YOUTUBE_FALLBACKS)
