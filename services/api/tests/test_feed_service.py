from __future__ import annotations

from datetime import datetime, timezone

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


def test_feed_interleaves_personalized_youtube_resource() -> None:
    feed = build_feed(_stack())

    resource = next(item for item in feed.items if item.kind == "resource")
    assert resource.tag == "YouTube"
    assert resource.channelTitle == "Trellis channel"
    assert resource.sourceBadge == "Live web"
    assert resource.explanation is not None


def test_feed_event_contract_allows_only_known_actions() -> None:
    assert FeedEventRequest(itemId="resource-video-1", event="opened").event == "opened"
