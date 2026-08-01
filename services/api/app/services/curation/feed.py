"""Assembly for the owned, personalized Growth Feed."""

from __future__ import annotations

from app.schemas.feed import FeedItem, FeedPage
from app.schemas.stack import IdentityStack, StackElement

_OWNED_CARDS: tuple[tuple[str, str, str], ...] = (
    ("low_value", "Trending", "9 desk setups that will change your life"),
    ("low_value", "Hustle", "He quit his job and now earns $40k/mo doing this"),
    ("neutral", "Craft", "A short read on writing clearer commit messages"),
    ("low_value", "Relatable", "POV: it is 2am and you are still scrolling"),
    ("low_value", "Clickbait", "You will not believe what happened next"),
    ("neutral", "Engineering", "Notes from a talk on system design tradeoffs"),
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


def build_feed(stack: IdentityStack | None) -> FeedPage:
    """Interleave owned cards with resources from the current personalized stack."""
    items: list[FeedItem] = []
    resources = [element for element in (stack.elements if stack else []) if element.type in {"media", "knowledge"}]
    resource_index = 0
    for index, (kind, tag, title) in enumerate(_OWNED_CARDS):
        items.append(FeedItem(id=f"owned-{index + 1}", kind=kind, tag=tag, title=title))
        if index in {1, 4} and resource_index < len(resources):
            items.append(_resource_item(resources[resource_index]))
            resource_index += 1
    while resource_index < len(resources):
        items.append(_resource_item(resources[resource_index]))
        resource_index += 1
    return FeedPage(items=items)
