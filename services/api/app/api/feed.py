"""Personalized, server-backed endpoints for the owned Growth Feed."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.di import (
    get_current_user_id,
    get_db,
    get_llm_provider,
    get_search_provider,
    get_youtube_provider,
)
from app.providers.llm.base import LLMProvider
from app.providers.search.base import SearchProvider
from app.providers.search.fake import FakeSearchProvider
from app.repositories import intervention_repository, twin_repository
from app.schemas.evidence import EvidenceIngestRequest
from app.schemas.feed import FeedEventRequest, FeedItem, FeedPage, PreparedFeedIntervention
from app.services.curation.feed import build_feed
from app.services.curation import stack_orchestration
from app.services.curation.trigger_refresh import enqueue_tier2_stack_refresh
from app.services.evidence import service as evidence_service

router = APIRouter(tags=["feed"])


def _stack_has_live_media(stack) -> bool:
    return any(
        element.type in {"media", "knowledge"}
        and element.sourceBadge in {"Live web", "Cached web"}
        for element in stack.elements
    )


def _active_or_create_stack(
    db: Session,
    user_id: str,
    search_provider: SearchProvider,
    llm_provider: LLMProvider,
    *,
    prefer_fresh_live: bool = False,
):
    active = intervention_repository.get_active(db, user_id)
    if active is not None:
        stack = intervention_repository.to_stack(active)
        # When live retrieval is configured, don't keep serving stacks built
        # under FakeSearchProvider / curated-only fixtures.
        if not prefer_fresh_live or _stack_has_live_media(stack):
            return stack
    return stack_orchestration.refresh_stack(db, user_id, search_provider, llm_provider)


@router.get("/feed", response_model=FeedPage)
def get_feed(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
    search_provider: SearchProvider = Depends(get_search_provider),
    youtube_provider: SearchProvider = Depends(get_youtube_provider),
    llm_provider: LLMProvider = Depends(get_llm_provider),
    settings: Settings = Depends(get_settings),
) -> FeedPage:
    live = settings.search_provider != "fake" and not isinstance(
        search_provider, FakeSearchProvider
    )
    stack = _active_or_create_stack(
        db,
        user_id,
        search_provider,
        llm_provider,
        prefer_fresh_live=live,
    )
    declared = twin_repository.get_active_declared_self(db, user_id)
    attribute_labels = (
        [attr.label for attr in declared.attributes if attr.label]
        if declared is not None
        else []
    )
    return build_feed(
        stack,
        search_provider=search_provider,
        youtube_provider=youtube_provider,
        user_id=user_id,
        attribute_labels=attribute_labels,
    )


@router.get("/feed/prepared-intervention", response_model=PreparedFeedIntervention)
def get_prepared_intervention(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
    search_provider: SearchProvider = Depends(get_search_provider),
    llm_provider: LLMProvider = Depends(get_llm_provider),
) -> PreparedFeedIntervention:
    stack = _active_or_create_stack(db, user_id, search_provider, llm_provider)
    if stack is None:
        raise HTTPException(status_code=404, detail="Complete onboarding before requesting interventions.")
    return PreparedFeedIntervention(stack=stack)


@router.post("/feed/events", response_model=FeedItem)
def record_feed_event(
    request: FeedEventRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
) -> FeedItem:
    # Viewing/opening/skipping is context only. Completing a purposeful resource
    # becomes passive-learning evidence through the same universal pipeline.
    is_completion = request.event == "completed"
    evidence_service.ingest(
        db,
        EvidenceIngestRequest(
            userId=user_id,
            timestamp=datetime.now(timezone.utc),
            source="trellis",
            type=f"feed_{request.event}",
            category="passive_learning" if is_completion else "reflection",
            value=1.0 if is_completion else 0.0,
            baseWeight=1.0 if is_completion else 0.0,
            metadata={"feed_item_id": request.itemId, **request.metadata},
            simulated=False,
        ),
    )
    if is_completion:
        enqueue_tier2_stack_refresh(user_id)
    # A compact acknowledgement keeps the endpoint useful for optimistic clients
    # without inventing a second telemetry persistence model.
    return FeedItem(id=request.itemId, kind="neutral", title=request.event, tag="logged")
