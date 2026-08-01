from __future__ import annotations

from datetime import datetime, timezone

from app.providers.search.base import Document
from app.providers.search.fake import FakeSearchProvider
from app.schemas.feed import FeedEventRequest
from app.schemas.stack import IdentityStack, StackElement, StackExplanation
from app.services.curation.feed import build_feed


def _stack() -> IdentityStack:
    explanation = StackExplanation(
        whyThis="Matches the current bottleneck.",
        whyNow="A short resource fits this moment.",
        howReducesGap="It supports an observable marker.",
    )
    return IdentityStack(
        id="stack-1",
        userId="user-1",
        hypothesisId="hyp-1",
        bottleneck="focus",
        curatedAt=datetime.now(timezone.utc),
        elements=[
            StackElement(
                id="video-1",
                type="media",
                title="A focused practice video",
                url="https://www.youtube.com/watch?v=abc",
                sourceBadge="Live web",
                explanation=explanation,
                metadata={
                    "video_id": "abc",
                    "channel_title": "Trellis channel",
                    "thumbnail_url": "https://img.youtube.com/vi/abc/hqdefault.jpg",
                },
            )
        ],
    )


def test_feed_includes_personalized_youtube_resource() -> None:
    feed = build_feed(_stack())

    resource = next(item for item in feed.items if item.kind == "resource")
    assert resource.tag == "YouTube"
    assert resource.channelTitle == "Trellis channel"
    assert resource.sourceBadge == "Live web"
    assert resource.explanation is not None


def test_feed_uses_live_search_documents_not_mock_headlines() -> None:
    youtube = FakeSearchProvider(
        [
            Document(
                title="Lex Fridman Podcast - AI and the future",
                url="https://www.youtube.com/watch?v=drift1",
                extract="Long-form tech podcast",
                source="youtube",
                metadata={
                    "video_id": "drift1",
                    "channel_title": "Lex Fridman",
                    "thumbnail_url": "https://img.youtube.com/vi/drift1/hqdefault.jpg",
                },
            ),
            Document(
                title="How music works - documentary interview",
                url="https://www.youtube.com/watch?v=drift2",
                extract="Music documentary",
                source="youtube",
                metadata={
                    "video_id": "drift2",
                    "channel_title": "Polyphonic",
                    "thumbnail_url": "https://img.youtube.com/vi/drift2/hqdefault.jpg",
                },
            ),
        ]
    )
    search = FakeSearchProvider(
        [
            Document(
                title="Writing clearer commit messages",
                url="https://example.org/commits",
                extract="Craft article from web search",
                source="tavily_live",
            )
        ]
    )

    feed = build_feed(_stack(), search_provider=search, youtube_provider=youtube)

    titles = {item.title for item in feed.items}
    assert "Lex Fridman Podcast - AI and the future" in titles
    assert "Writing clearer commit messages" in titles
    assert "POV: it is 2am and you are still scrolling" not in titles
    assert any(item.kind == "low_value" and item.thumbnailUrl for item in feed.items)
    assert any(item.kind == "neutral" and item.sourceBadge == "Live web" for item in feed.items)


def test_feed_filters_short_form_clickbait_titles() -> None:
    youtube = FakeSearchProvider(
        [
            Document(
                title="Excuse me baat sune madam reaction 😂 #shorts",
                url="https://www.youtube.com/watch?v=junk1",
                extract="junk",
                source="youtube",
                metadata={"video_id": "junk1", "thumbnail_url": "https://img.youtube.com/vi/junk1/hqdefault.jpg"},
            ),
            Document(
                title="The Future of Computing | TED Talk",
                url="https://www.youtube.com/watch?v=good1",
                extract="ted",
                source="youtube",
                metadata={"video_id": "good1", "thumbnail_url": "https://img.youtube.com/vi/good1/hqdefault.jpg"},
            ),
        ]
    )

    feed = build_feed(None, youtube_provider=youtube)
    titles = {item.title for item in feed.items}
    assert "The Future of Computing | TED Talk" in titles
    assert not any("#shorts" in title.lower() for title in titles)


def test_feed_event_contract_allows_only_known_actions() -> None:
    assert FeedEventRequest(itemId="resource-video-1", event="opened").event == "opened"
