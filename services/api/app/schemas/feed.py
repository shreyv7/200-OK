"""Server-backed Growth Feed contracts.

The feed is an owned Trellis surface.  Third-party resources such as YouTube
are recommendation cards within it, never an imported third-party feed.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from app.schemas.stack import IdentityStack, SourceBadge, StackExplanation


FeedItemKind = Literal["low_value", "neutral", "resource"]
FeedEventType = Literal["viewed", "opened", "skipped", "completed"]


class FeedItem(BaseModel):
    id: str
    kind: FeedItemKind
    title: str
    tag: str
    url: str | None = None
    sourceBadge: SourceBadge | None = None
    thumbnailUrl: str | None = None
    channelTitle: str | None = None
    durationSeconds: int | None = None
    explanation: StackExplanation | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class FeedPage(BaseModel):
    items: list[FeedItem]
    nextCursor: str | None = None


class PreparedFeedIntervention(BaseModel):
    stack: IdentityStack


class FeedEventRequest(BaseModel):
    itemId: str
    event: FeedEventType
    metadata: dict[str, Any] = Field(default_factory=dict)
