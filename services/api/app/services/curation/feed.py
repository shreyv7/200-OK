"""Assembly for the owned, personalized Growth Feed.

Scroll cards are live YouTube / Tavily (or labeled curated fallbacks) —
never hardcoded mock headlines. Personalized Identity Stack media/knowledge
cards are interleaved as `resource` items.
"""

from __future__ import annotations

from app.providers.search.base import Document, SearchProvider
from app.schemas.feed import FeedItem, FeedPage
from app.schemas.stack import IdentityStack, StackElement
from app.services.curation.spotify_playlists import playlists_as_feed_items
from app.services.recommendation.badge_mapping import document_source_to_badge

# Hackathon-facing YouTube queries: intellectual / tech / podcast / music.
# Still labeled low_value for Moment Detector (passive scroll during focus).
_PASSIVE_QUERIES: tuple[str, ...] = (
    "Lex Fridman podcast artificial intelligence interview",
    "TED talk technology science innovation",
    "music theory documentary classical jazz interview",
    "software engineering systems design conference talk",
)
_NEUTRAL_QUERY = "software engineering craft productivity deep work tutorial"

# Drop obvious short-form clickbait even if the API returns them.
_JUNK_TITLE_MARKERS: tuple[str, ...] = (
    "#shorts",
    "#short",
    "try not to laugh",
    "prank",
    "funny video",
    "viralshort",
    "reaction 😂",
    "gone wrong",
    "you won't believe",
)


def _resource_item(element: StackElement) -> FeedItem:
    metadata = element.metadata or {}
    return FeedItem(
        id=f"resource-{element.id}",
        kind="resource",
        title=element.title,
        tag="YouTube" if metadata.get("video_id") else element.type.replace("_", " ").title(),
        url=element.url,
        sourceBadge=element.sourceBadge,
        thumbnailUrl=metadata.get("thumbnail_url"),
        channelTitle=metadata.get("channel_title"),
        durationSeconds=metadata.get("duration_seconds"),
        explanation=element.explanation,
        metadata=metadata,
    )


def _document_item(document: Document, *, kind: str, prefix: str, index: int) -> FeedItem:
    metadata = dict(document.metadata or {})
    video_id = metadata.get("video_id")
    if not video_id and "youtube.com/watch" in document.url:
        # Recover id from watch URLs when providers omit metadata.
        marker = "v="
        if marker in document.url:
            video_id = document.url.split(marker, 1)[1].split("&", 1)[0]
            metadata["video_id"] = video_id
            metadata.setdefault(
                "thumbnail_url",
                f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg",
            )

    is_youtube = bool(metadata.get("video_id"))
    if is_youtube:
        tag = "YouTube"
    elif "tavily" in document.source:
        tag = "Web"
    else:
        tag = "Curated"

    return FeedItem(
        id=f"{prefix}-{index + 1}",
        kind=kind,  # type: ignore[arg-type]
        title=document.title,
        tag=tag,
        url=document.url,
        sourceBadge=document_source_to_badge(document.source),
        thumbnailUrl=metadata.get("thumbnail_url"),
        channelTitle=metadata.get("channel_title"),
        durationSeconds=metadata.get("duration_seconds"),
        metadata=metadata,
    )


def _is_junk_title(title: str) -> bool:
    lowered = title.lower()
    return any(marker in lowered for marker in _JUNK_TITLE_MARKERS)


def _safe_search(
    provider: SearchProvider | None,
    query: str,
    *,
    max_results: int,
    quality: bool = False,
) -> list[Document]:
    if provider is None:
        return []
    opts: dict = {"max_results": max_results}
    if quality:
        # medium = 4–20 minutes — skips Shorts-style clips.
        opts.update(
            {
                "videoDuration": "medium",
                "relevanceLanguage": "en",
                "safeSearch": "strict",
            }
        )
    try:
        return list(provider.search(query, opts) or [])
    except Exception:
        return []


def _dedupe_docs(documents: list[Document], *, seen: set[str]) -> list[Document]:
    unique: list[Document] = []
    for document in documents:
        key = document.url.strip()
        if not key or key in seen:
            continue
        if _is_junk_title(document.title):
            continue
        seen.add(key)
        unique.append(document)
    return unique


def _fetch_quality_videos(
    provider: SearchProvider | None,
    *,
    seen: set[str],
    limit: int,
) -> list[Document]:
    """Round-robin high-signal YouTube queries until we have enough videos."""
    collected: list[Document] = []
    # Take a small slice from each theme so the phone feed mixes
    # podcasts / TED / music / engineering instead of one channel cluster.
    per_query = 2
    for query in _PASSIVE_QUERIES:
        docs = _dedupe_docs(
            _safe_search(provider, query, max_results=per_query + 1, quality=True),
            seen=seen,
        )
        videos = [
            d for d in docs if (d.metadata or {}).get("video_id") or "youtube.com" in d.url
        ]
        collected.extend(videos[:per_query])
        if len(collected) >= limit:
            break
    return collected[:limit]


def build_feed(
    stack: IdentityStack | None,
    *,
    search_provider: SearchProvider | None = None,
    youtube_provider: SearchProvider | None = None,
    user_id: str | None = None,
    attribute_labels: list[str] | None = None,
) -> FeedPage:
    """Build a feed from live retrieval + personalized stack resources.

    - `low_value`: quality passive media (podcasts / TED / tech / music) for Catch
    - `neutral`: real Tavily/YouTube craft / learning content
    - `resource`: personalized Identity Stack media/knowledge + Spotify playlists
    """
    seen: set[str] = set()
    for element in stack.elements if stack else []:
        if element.url:
            seen.add(element.url.strip())

    drift_provider = youtube_provider or search_provider
    drift_pool = _fetch_quality_videos(drift_provider, seen=seen, limit=6)

    # If live YouTube is exhausted, still paint the phone with curated videos.
    if len(drift_pool) < 3 and youtube_provider is not None:
        try:
            fallback = getattr(youtube_provider, "get_fallback", None)
            curated = list(fallback(_PASSIVE_QUERIES[0]) if callable(fallback) else [])
        except Exception:
            curated = []
        drift_pool.extend(_dedupe_docs(curated, seen=seen))
        drift_pool = drift_pool[:6]

    neutral_docs = _dedupe_docs(
        _safe_search(
            search_provider or youtube_provider,
            _NEUTRAL_QUERY,
            max_results=6,
            quality=True,
        ),
        seen=seen,
    )
    if len(neutral_docs) < 2 and search_provider is not None:
        try:
            fallback = getattr(search_provider, "get_fallback", None)
            if not callable(fallback) and youtube_provider is not None:
                fallback = getattr(youtube_provider, "get_fallback", None)
            curated = list(fallback(_NEUTRAL_QUERY) if callable(fallback) else [])
        except Exception:
            curated = []
        neutral_docs.extend(_dedupe_docs(curated, seen=seen))

    low_value_items = [
        _document_item(doc, kind="low_value", prefix="drift", index=i)
        for i, doc in enumerate(drift_pool)
    ]
    neutral_items = [
        _document_item(doc, kind="neutral", prefix="craft", index=i)
        for i, doc in enumerate(neutral_docs[:3])
    ]

    resources = [
        _resource_item(element)
        for element in (stack.elements if stack else [])
        if element.type in {"media", "knowledge"}
    ]

    # Persona-specific Spotify deep-links (no OAuth) — stable per user.
    # Always include playlists; thumbnail/network failures must not drop cards.
    spotify_user = user_id or (stack.userId if stack else "anonymous")
    try:
        spotify_items = playlists_as_feed_items(
            spotify_user,
            bottleneck=stack.bottleneck if stack else None,
            attribute_labels=attribute_labels,
            count=2,
        )
    except Exception:
        spotify_items = []
    resources = [*resources, *spotify_items]

    # Interleave so Moment Detector can still see a low-value majority while
    # personalized YouTube/web/Spotify resources appear in-stream.
    items: list[FeedItem] = []
    li = ni = ri = 0
    pattern = ("low_value", "low_value", "resource", "low_value", "neutral", "resource")
    while li < len(low_value_items) or ni < len(neutral_items) or ri < len(resources):
        progressed = False
        for slot in pattern:
            if slot == "low_value" and li < len(low_value_items):
                items.append(low_value_items[li])
                li += 1
                progressed = True
            elif slot == "neutral" and ni < len(neutral_items):
                items.append(neutral_items[ni])
                ni += 1
                progressed = True
            elif slot == "resource" and ri < len(resources):
                items.append(resources[ri])
                ri += 1
                progressed = True
        if not progressed:
            break

    return FeedPage(items=items)
