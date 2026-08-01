from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.schemas import DecisionPacket
from app.services.recommendation.onboarding_hook import on_onboarding_confirmed
from app.services.recommendation.stack_state import clear_stack_state, get_active_stack
from app.services.recommendation.warm_cache import warm_cache_after_onboarding
from tests.conftest import ensure_user
from tests.fixtures.sample_data import sample_onboarding_confirm_event


def test_warm_cache_search_failure_still_succeeds_with_fallback(db_session) -> None:
    """M4: retrieval failures degrade to seeded stack; warm-cache must not block onboarding."""
    clear_stack_state()
    ensure_user(db_session, "user-aarav")
    packet = DecisionPacket(userId="user-aarav", gapDelta=0.0, invalidateStack=True)
    failing_search = MagicMock()
    failing_search.search.side_effect = RuntimeError("search down")

    result = warm_cache_after_onboarding(
        db_session,
        "user-aarav",
        packet,
        search=failing_search,
    )

    assert result.ok is True
    stack = get_active_stack("user-aarav")
    assert stack is not None
    assert any(element.sourceBadge == "Curated fallback" for element in stack.elements)


def test_warm_cache_catastrophic_failure_does_not_raise(db_session) -> None:
    ensure_user(db_session, "user-aarav")
    packet = DecisionPacket(userId="user-aarav", gapDelta=0.0, invalidateStack=True)

    with patch(
        "app.services.recommendation.warm_cache.stack_orchestration.run_curation_and_persist",
        side_effect=RuntimeError("graph down"),
    ):
        result = warm_cache_after_onboarding(db_session, "user-aarav", packet)

    assert result.ok is False
    assert "graph down" in (result.reason or "")


def test_onboarding_confirm_succeeds_when_warm_cache_fails(monkeypatch, db_session) -> None:
    clear_stack_state()
    ensure_user(db_session, "user-aarav")
    event = sample_onboarding_confirm_event(with_gap_snapshot=False)

    def _fail_warm_cache(*_args, **_kwargs):
        from app.services.recommendation.warm_cache import WarmCacheResult

        return WarmCacheResult(ok=False, reason="forced failure")

    monkeypatch.setattr(
        "app.services.recommendation.onboarding_hook.warm_cache_after_onboarding",
        _fail_warm_cache,
    )

    result = on_onboarding_confirmed(event, db=db_session)

    assert "coordinator" in result["visited"]
    assert result["warm_cache"]["ok"] is False
    assert result["warm_cache"]["reason"] == "forced failure"
