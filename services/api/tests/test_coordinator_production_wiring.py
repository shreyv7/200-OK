from __future__ import annotations

from datetime import datetime
from unittest.mock import patch

from app.agents.graphs.coordinator import build_coordinator_graph
from app.core.config import get_settings
from app.core.di import get_llm_provider, get_search_provider
from app.repositories import intervention_repository, twin_repository
from app.services.curation import stack_orchestration
from app.services.recommendation.stack_state import clear_stack_state
from app.workers.seed import _DECLARED_ATTRIBUTES
from tests.conftest import ensure_user
from tests.fixtures.sample_data import sample_decision_packet_with_bottleneck


def _ensure_demo_twin(db_session) -> str:
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
    return user_id


def test_refresh_stack_uses_coordinator_graph(db_session) -> None:
    clear_stack_state()
    user_id = _ensure_demo_twin(db_session)
    settings = get_settings()
    search = get_search_provider(settings)
    llm = get_llm_provider(settings)

    visited: list[str] = []
    real_graph = build_coordinator_graph()
    original_invoke = real_graph.invoke

    def tracked_invoke(state):
        result = original_invoke(state)
        visited.extend(result.get("visited", []))
        return result

    mock_graph = type("MockGraph", (), {"invoke": staticmethod(tracked_invoke)})()

    with patch(
        "app.services.recommendation.curation_cycle.build_coordinator_graph",
        return_value=mock_graph,
    ):
        stack = stack_orchestration.refresh_stack(db_session, user_id, search, llm)

    assert stack is not None
    assert "coordinator" in visited
    assert "assemble" in visited

    row = intervention_repository.get_active(db_session, user_id)
    assert row is not None
    variants = intervention_repository.to_variants(row)
    assert set(variants.keys()) == {"full", "light", "micro"}


def test_run_curation_and_persist_persists_variants(db_session) -> None:
    clear_stack_state()
    user_id = _ensure_demo_twin(db_session)
    settings = get_settings()
    search = get_search_provider(settings)
    llm = get_llm_provider(settings)

    packet = sample_decision_packet_with_bottleneck()
    stack = stack_orchestration.run_curation_and_persist(
        db_session,
        user_id,
        packet,
        search,
        llm,
        trigger="stack.refresh",
    )

    assert stack is not None
    row = intervention_repository.get_active(db_session, user_id)
    assert row is not None
    assert row.hypothesis_id == stack.hypothesisId
