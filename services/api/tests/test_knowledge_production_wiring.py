from __future__ import annotations

from unittest.mock import patch

from app.agents.nodes.knowledge.node import knowledge_node
from app.providers.search.base import Document
from app.providers.search.fake import FakeSearchProvider
from app.services.recommendation.knowledge_retrieval import retrieve_knowledge_candidates
from tests.conftest import ensure_user


class _RaisingSearchProvider(FakeSearchProvider):
    def search(self, query: str, opts=None):  # type: ignore[no-untyped-def]
        raise TimeoutError("live search timeout")


def test_retrieve_knowledge_with_db_uses_retrieval_chain(db_session) -> None:
    ensure_user(db_session, "user-kr-chain")
    provider = FakeSearchProvider(
        documents=[
            Document(
                title="Execution focus guide",
                url="https://example.com/focus",
                extract="A guide for execution bottleneck.",
                source="tavily_live",
            )
        ]
    )

    with patch(
        "app.services.recommendation.knowledge_retrieval.search_with_fallback"
    ) as mock_chain:
        mock_chain.return_value = (
            [
                Document(
                    title="Cached execution article",
                    url="https://example.com/cached",
                    extract="Cached hit.",
                    source="resource_cache",
                )
            ],
            "Cached web",
        )
        candidates = retrieve_knowledge_candidates(
            "execution",
            search=provider,
            user_id="user-kr-chain",
            db=db_session,
        )

    mock_chain.assert_called_once()
    assert candidates
    assert candidates[0]["sourceBadge"] == "Cached web"


def test_retrieve_knowledge_without_db_skips_retrieval_chain() -> None:
    provider = FakeSearchProvider(
        documents=[
            Document(
                title="Live article",
                url="https://example.com/live",
                extract="Live hit.",
                source="tavily_live",
            )
        ]
    )

    with patch(
        "app.services.recommendation.knowledge_retrieval.search_with_fallback"
    ) as mock_chain:
        candidates = retrieve_knowledge_candidates("execution", search=provider)

    mock_chain.assert_not_called()
    assert candidates[0]["sourceBadge"] == "Live web"


def test_knowledge_node_passes_db_session_to_retrieval(db_session) -> None:
    ensure_user(db_session, "user-kr-node")
    state = {
        "bottleneck_packet": {"bottleneck": "execution"},
        "decision_packet": {"rankingFeatures": {"alignment": 42}},
        "user_id": "user-kr-node",
        "db_session": db_session,
        "search_provider": _RaisingSearchProvider(),
    }

    with patch(
        "app.agents.nodes.knowledge.node.retrieve_knowledge_candidates"
    ) as mock_retrieve:
        mock_retrieve.return_value = [{"id": "c1", "type": "media", "title": "T", "sourceBadge": "Curated fallback"}]
        result = knowledge_node(state)

    mock_retrieve.assert_called_once()
    kwargs = mock_retrieve.call_args.kwargs
    assert kwargs["db"] is db_session
    assert kwargs["ranking_features"] == {"alignment": 42}
    assert "knowledge" in result["visited"]


def test_production_refresh_stack_knowledge_uses_db_chain(db_session) -> None:
    from datetime import datetime

    from app.core.config import get_settings
    from app.core.di import get_llm_provider, get_search_provider
    from app.repositories import twin_repository
    from app.services.curation import stack_orchestration
    from app.services.recommendation.stack_state import clear_stack_state
    from app.workers.seed import _DECLARED_ATTRIBUTES

    clear_stack_state()
    settings = get_settings()
    user_id = settings.demo_user_id
    ensure_user(db_session, user_id)
    if twin_repository.get_active_declared_self(db_session, user_id) is None:
        twin_repository.create_version(
            db_session,
            user_id=user_id,
            version=1,
            attributes=_DECLARED_ATTRIBUTES,
            confirmed_at=datetime.utcnow(),
        )

    with patch(
        "app.services.recommendation.knowledge_retrieval.search_with_fallback"
    ) as mock_chain:
        mock_chain.return_value = (
            [
                Document(
                    title="Chain-backed resource",
                    url="https://example.com/chain",
                    extract="From retrieval chain.",
                    source="resource_cache",
                )
            ],
            "Cached web",
        )
        stack = stack_orchestration.refresh_stack(
            db_session,
            user_id,
            get_search_provider(settings),
            get_llm_provider(settings),
        )

    assert stack is not None
    mock_chain.assert_called()
    assert any(
        element.sourceBadge == "Cached web"
        for element in stack.elements
        if element.type in {"media", "knowledge"}
    )
