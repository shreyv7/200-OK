from __future__ import annotations

from unittest.mock import patch

from app.agents.nodes.planner.node import planner_node
from app.repositories import ledger_repository
from app.services.recommendation.lens_weights import clear_lens_weights, set_lens_weights
from app.services.recommendation.planner_missions import (
    MISSION_TEMPLATES,
    build_planner_candidates,
    resolve_small_experiment,
)
from tests.conftest import ensure_user


def test_build_planner_candidates_covers_all_bottleneck_labels() -> None:
    for label in MISSION_TEMPLATES:
        candidates = build_planner_candidates(label)
        assert len(candidates) == 1
        assert candidates[0]["type"] == "micro_mission"
        assert candidates[0]["metadata"]["bottleneck"] == label


def test_resolve_small_experiment_from_low_confidence() -> None:
    assert resolve_small_experiment(
        small_experiment=False,
        bottleneck_confidence=0.3,
        lens_weights={"media": 0.4, "micro_mission": 0.4},
    )


def test_resolve_small_experiment_from_unlearning_lens_weights() -> None:
    assert resolve_small_experiment(
        small_experiment=False,
        bottleneck_confidence=0.9,
        lens_weights={"media": 0.1, "micro_mission": 0.5, "knowledge": 0.4},
    )


def test_build_planner_candidates_uses_ledger_lens_weights(db_session) -> None:
    ensure_user(db_session, "user-planner-ledger")
    ledger_repository.record(
        db_session,
        user_id="user-planner-ledger",
        hypothesis_id="hyp-planner-1",
        hypothesis_family="media-video",
        action="dismissed",
        verdict="failed",
        unlearning_triggered=True,
        lens_weight_adjustment={"media": -0.35},
    )

    candidates = build_planner_candidates(
        "execution",
        user_id="user-planner-ledger",
        db=db_session,
    )

    assert candidates[0]["title"].startswith("Small experiment:")
    assert candidates[0]["metadata"]["smallExperiment"] is True


def test_build_planner_candidates_falls_back_to_in_memory_lens_weights() -> None:
    clear_lens_weights()
    set_lens_weights("user-planner-mem", {"media": 0.05, "micro_mission": 0.6, "knowledge": 0.35})

    candidates = build_planner_candidates("focus", user_id="user-planner-mem")

    assert candidates[0]["metadata"]["smallExperiment"] is True
    assert "distraction-free" in candidates[0]["title"].lower()


def test_planner_node_passes_db_session_and_confidence(db_session) -> None:
    ensure_user(db_session, "user-planner-node")
    state = {
        "bottleneck_packet": {"bottleneck": "networking", "confidence": 0.35},
        "user_id": "user-planner-node",
        "db_session": db_session,
    }

    with patch(
        "app.agents.nodes.planner.node.build_planner_candidates"
    ) as mock_build:
        mock_build.return_value = [{"id": "m1", "type": "micro_mission", "title": "T"}]
        result = planner_node(state)

    mock_build.assert_called_once()
    kwargs = mock_build.call_args.kwargs
    assert kwargs["db"] is db_session
    assert kwargs["bottleneck_confidence"] == 0.35
    assert kwargs["user_id"] == "user-planner-node"
    assert "planner" in result["visited"]


def test_production_refresh_stack_includes_planner_mission(db_session) -> None:
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

    stack = stack_orchestration.refresh_stack(
        db_session,
        user_id,
        get_search_provider(settings),
        get_llm_provider(settings),
    )

    assert stack is not None
    missions = [element for element in stack.elements if element.type == "micro_mission"]
    assert len(missions) >= 1
    assert missions[0].title
