"""YouTube Data API v3 media provider. Owner: Backend (work.md C2).

Fetches video metadata when a lens needs video/media content (e.g. Next Step /
knowledge lens). Falls back to curated media if API key is absent, rate-limited,
or timed out. Keys rotate on 403/429 so exhausted quotas do not empty the feed.
"""

from __future__ import annotations

from typing import Any

import httpx

from app.providers.search.base import Document, SearchProvider


_CURATED_YOUTUBE_FALLBACKS: list[Document] = [
    Document(
        title="How to Get Your Brain to Focus | Chris Bailey | TEDxManchester",
        url="https://www.youtube.com/watch?v=Hu4Yvq-g7_Y",
        extract="Practical focus strategies for a distracted world.",
        source="curated_youtube_fallback",
        metadata={
            "video_id": "Hu4Yvq-g7_Y",
            "channel_title": "TEDx Talks",
            "thumbnail_url": "https://img.youtube.com/vi/Hu4Yvq-g7_Y/hqdefault.jpg",
        },
    ),
    Document(
        title="How to Build a Second Brain",
        url="https://www.youtube.com/watch?v=OP3dA2GcAh8",
        extract="Methodology for capturing, organizing, and distilling personal knowledge.",
        source="curated_youtube_fallback",
        metadata={
            "video_id": "OP3dA2GcAh8",
            "channel_title": "Ali Abdaal",
            "thumbnail_url": "https://img.youtube.com/vi/OP3dA2GcAh8/hqdefault.jpg",
        },
    ),
    Document(
        title="The Art of Code - Dylan Beattie",
        url="https://www.youtube.com/watch?v=6avJHaC3C2U",
        extract="A talk on programming as creative craft — music, language, and software.",
        source="curated_youtube_fallback",
        metadata={
            "video_id": "6avJHaC3C2U",
            "channel_title": "NDC Conferences",
            "thumbnail_url": "https://img.youtube.com/vi/6avJHaC3C2U/hqdefault.jpg",
        },
    ),
    Document(
        title="Deep Work: Rules for Focused Success in a Distracted World",
        url="https://www.youtube.com/watch?v=fgXF5H-5c0I",
        extract="Cal Newport on building focus as a competitive advantage.",
        source="curated_youtube_fallback",
        metadata={
            "video_id": "fgXF5H-5c0I",
            "channel_title": "Author Talks",
            "thumbnail_url": "https://img.youtube.com/vi/fgXF5H-5c0I/hqdefault.jpg",
        },
    ),
    Document(
        title="Lex Fridman Podcast — Conversations that Matter",
        url="https://www.youtube.com/watch?v=DxREm3s1scA",
        extract="Long-form interview energy for intellectual passive scroll.",
        source="curated_youtube_fallback",
        metadata={
            "video_id": "DxREm3s1scA",
            "channel_title": "Lex Fridman",
            "thumbnail_url": "https://img.youtube.com/vi/DxREm3s1scA/hqdefault.jpg",
        },
    ),
]


class YouTubeMediaProvider(SearchProvider):
    def __init__(self, api_key: str | list[str] | None = None, timeout_seconds: float = 2.0) -> None:
        self._timeout_seconds = timeout_seconds
        self._endpoint = "https://www.googleapis.com/youtube/v3/search"
        if isinstance(api_key, list):
            self._api_keys = [k.strip() for k in api_key if k and k.strip()]
        elif isinstance(api_key, str) and api_key.strip():
            self._api_keys = [k.strip() for k in api_key.split(",") if k.strip()]
        else:
            self._api_keys = []

    @property
    def _api_key(self) -> str | None:
        return self._api_keys[0] if self._api_keys else None

    def _promote_key(self, key: str) -> None:
        """Keep a working key at the front so subsequent queries skip burned ones."""
        if key not in self._api_keys:
            return
        self._api_keys = [key, *[k for k in self._api_keys if k != key]]

    def _demote_key(self, key: str) -> None:
        """Push exhausted / rate-limited keys to the end of the rotation."""
        if key not in self._api_keys or len(self._api_keys) < 2:
            return
        self._api_keys = [*[k for k in self._api_keys if k != key], key]

    def search(self, query: str, opts: dict[str, Any] | None = None) -> list[Document]:
        if not self._api_keys:
            return self.get_fallback(query)

        opts = opts or {}
        max_results = opts.get("max_results", 5)
        # Prefer longer-form videos over Shorts when callers ask for quality feed.
        video_duration = opts.get("videoDuration", "any")
        safe_search = opts.get("safeSearch", "moderate")
        relevance_language = opts.get("relevanceLanguage")
        video_category_id = opts.get("videoCategoryId")

        # Snapshot order so demotions during the loop don't skip keys.
        for key in list(self._api_keys):
            params: dict[str, Any] = {
                "part": "snippet",
                "type": "video",
                "q": query,
                "maxResults": max_results,
                "key": key,
                "safeSearch": safe_search,
            }
            if video_duration and video_duration != "any":
                params["videoDuration"] = video_duration
            if relevance_language:
                params["relevanceLanguage"] = relevance_language
            if video_category_id:
                params["videoCategoryId"] = video_category_id

            try:
                with httpx.Client(timeout=self._timeout_seconds) as client:
                    res = client.get(self._endpoint, params=params)
                    if res.status_code in {401, 403, 429}:
                        self._demote_key(key)
                        continue
                    if res.status_code != 200:
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
                    self._promote_key(key)
                    return documents

            except Exception:
                self._demote_key(key)
                continue

        return self.get_fallback(query)

    def get_fallback(self, query: str) -> list[Document]:
        return list(_CURATED_YOUTUBE_FALLBACKS)
