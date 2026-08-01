from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import patch

from app.agents.nodes.guardian.node import guardian_node
from app.agents.nodes.reflection.node import reflection_node
from app.repositories import budget_repository
from app.services.recommendation.guardian_gate import (
    apply_guardian_gate,
    build_guardian_context,
    guardian_context_from_state,
)
from app.services.recommendation.guardian import GuardianContext
from app.services.recommendation.ledger_intake import clear_intake_store, get_pending_window
from app.services.recommendation.reflection_ledger import attach_evidence, process_ledger_action
from tests.conftest import ensure_user
from tests.fixtures.sample_data import sample_active_stack_for_variants


def test_build_guardian_context_from_db(db_session) -> None:
    from app.models.user import User

    ensure_user(db_session, "user-guardian-ctx")
    user = db_session.get(User, "user-guardian-ctx")
    assert user is not None
    user.capacity = 35.0
    db_session.commit()

    budget_repository.record_intervention_delivered(db_session, "user-guardian-ctx")

    context = build_guardian_context(db_session, "user-guardian-ctx")

    assert context.capacity_pct == 35
    assert context.interventions_today == 1
    assert context.last_intervention_at is not None


def test_apply_guardian_gate_downgrades_low_capacity() -> None:
    stack = sample_active_stack_for_variants()
    result = apply_guardian_gate(stack, GuardianContext(capacity_pct=20))

    assert result.delivery_allowed is True
    assert result.decision.intensity == "micro"
    assert result.stack is not None
    assert len(result.stack.elements) == 1


def test_guardian_node_uses_guardian_gate_module() -> None:
    stack = sample_active_stack_for_variants()
    state = {
        "identity_stack": stack.model_dump(),
        "capacity_pct": 100,
        "interventions_today": 0,
        "recent_dismissal_rate": 0.0,
    }

    with patch("app.agents.nodes.guardian.node.apply_guardian_gate") as mock_apply:
        mock_apply.return_value = apply_guardian_gate(
            stack,
            guardian_context_from_state(state),
        )
        result = guardian_node(state)

    mock_apply.assert_called_once()
    assert "guardian" in result["visited"]
    assert result["delivery_allowed"] is True


def test_process_ledger_action_persists_and_trips_unlearning(db_session) -> None:
    ensure_user(db_session, "user-reflect-unlearn")
    family = "media-video-unlearn"

    process_ledger_action("user-reflect-unlearn", "hyp-1", family, "dismissed", db=db_session)
    process_ledger_action("user-reflect-unlearn", "hyp-1", family, "dismissed", db=db_session)
    result = process_ledger_action(
        "user-reflect-unlearn", "hyp-1", family, "dismissed", db=db_session
    )

    assert result.ledger_entry.verdict == "failed"
    assert result.ledger_entry.unlearningTriggered is True
    assert result.alternate_stack is not None
    assert all(element.type != "media" for element in result.alternate_stack.elements)


def test_reflection_node_reads_hypothesis_from_stack() -> None:
    clear_intake_store()
    stack = sample_active_stack_for_variants()
    state = {
        "identity_stack": stack.model_dump(),
        "evidence_id": "ev-stack-001",
    }

    reflection_node(state)

    assert "ev-stack-001" in get_pending_window(stack.hypothesisId)


def test_attach_evidence_is_reflection_module_entrypoint() -> None:
    clear_intake_store()
    attach_evidence("hyp-attach", ["ev-a"])
    assert get_pending_window("hyp-attach") == ["ev-a"]


def test_production_refresh_records_guardian_delivery_budget(db_session) -> None:
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
            confirmed_at=datetime.now(timezone.utc),
        )

    before = budget_repository.get_or_create(db_session, user_id).interventions_today
    stack_orchestration.refresh_stack(
        db_session,
        user_id,
        get_search_provider(settings),
        get_llm_provider(settings),
    )
    after = budget_repository.get_or_create(db_session, user_id).interventions_today

    assert after == before + 1
