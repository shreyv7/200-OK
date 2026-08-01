from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from app.services.recommendation.knowledge_retrieval import (
    retrieve_knowledge_candidates,
    score_developmental_fit,
)
from app.agents.nodes.opportunity.node import retrieve_opportunity_candidates
from app.providers.search.base import Document, SearchProvider
from app.schemas import BottleneckPacket, DecisionPacket

from app.services.recommendation.stack_assembler import assemble_identity_stack


class _MockLiveSearchProvider(SearchProvider):
    def __init__(self, docs: list[Document]) -> None:
        self.docs = docs

    def search(self, query: str, opts: dict[str, Any] | None = None) -> list[Document]:
        return self.docs


class _FailingSearchProvider(SearchProvider):
    def search(self, query: str, opts: dict[str, Any] | None = None) -> list[Document]:
        raise RuntimeError("Search service unavailable")


def test_score_developmental_fit_calculates_correct_scores() -> None:
    live_doc = Document(
        title="Execution Guide for Focus",
        url="https://example.com/execution-guide",
        extract="A strategy to fix execution bottleneck and build focus habits.",
        source="tavily_live",
    )
    fallback_doc = Document(
        title="General Article",
        url="https://example.com/general",
        extract="Unrelated content.",
        source="curated_fallback",
    )

    live_score = score_developmental_fit(live_doc, "execution")
    fallback_score = score_developmental_fit(fallback_doc, "execution")

    assert live_score > fallback_score
    assert live_score >= 1.0


def test_retrieve_knowledge_candidates_ranks_by_developmental_fit() -> None:
    doc1 = Document(
        title="General Overview",
        url="https://example.com/1",
        extract="General overview of work.",
        source="tavily_live",
    )
    doc2 = Document(
        title="Execution Strategy for Focus Bottleneck",
        url="https://example.com/2",
        extract="Specific guide to solve execution bottleneck.",
        source="tavily_live",
    )
    provider = _MockLiveSearchProvider([doc1, doc2])

    candidates = retrieve_knowledge_candidates("execution", search=provider)

    assert len(candidates) == 2
    # doc2 should be ranked first due to bottleneck keyword match score boost
    assert candidates[0]["title"] == "Execution Strategy for Focus Bottleneck"
    assert candidates[0]["sourceBadge"] == "Live web"


def test_retrieve_opportunity_candidates_returns_live_or_fallback() -> None:
    doc = Document(
        title="Pune Tech Meetup for Execution",
        url="https://example.com/pune-meetup",
        extract="Event details in Pune.",
        source="tavily_live",
    )
    live_provider = _MockLiveSearchProvider([doc])

    live_candidates = retrieve_opportunity_candidates("execution", search=live_provider)
    assert len(live_candidates) == 1
    assert live_candidates[0]["sourceBadge"] == "Live web"
    assert live_candidates[0]["title"] == "Pune Tech Meetup for Execution"

    # Failing provider falls back to Pune events fallback
    failing_candidates = retrieve_opportunity_candidates("execution", search=_FailingSearchProvider())
    assert len(failing_candidates) >= 1
    assert failing_candidates[0]["sourceBadge"] == "Curated fallback"


def test_assemble_identity_stack_uses_top_ranked_next_step_candidate() -> None:
    packet = DecisionPacket(
        userId="user-test-c3",
        gapDelta=-0.1,
        bottleneck=BottleneckPacket(bottleneck="focus", confidence=0.9),
    )


    knowledge_cands = [
        {
            "id": "cand-media-0",
            "type": "media",
            "title": "Live Focus Strategy Guide",
            "url": "https://example.com/live-focus",
            "sourceBadge": "Live web",
            "extract": "Deep focus guide.",
        }
    ]
    planner_cands = [
        {
            "id": "cand-mission-focus",
            "type": "micro_mission",
            "title": "Protect one 25-minute focus block",
            "sourceBadge": "Curated fallback",
        }
    ]

    stack = assemble_identity_stack(
        packet,
        knowledge_candidates=knowledge_cands,
        planner_candidates=planner_cands,
    )

    assert len(stack.elements) >= 2
    assert stack.elements[0].title == "Protect one 25-minute focus block"
    assert stack.elements[1].title == "Live Focus Strategy Guide"
    assert stack.elements[1].sourceBadge == "Live web"
