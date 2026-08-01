from __future__ import annotations

from unittest.mock import MagicMock

from app.schemas import DecisionPacket
from app.services.recommendation.onboarding_hook import on_onboarding_confirmed
from app.services.recommendation.stack_state import clear_stack_state
from app.services.recommendation.warm_cache import warm_cache_after_onboarding
from tests.fixtures.sample_data import sample_onboarding_confirm_event


def test_warm_cache_failure_does_not_raise() -> None:
    packet = DecisionPacket(userId="user-aarav", gapDelta=0.0, invalidateStack=True)
    failing_search = MagicMock()
    failing_search.search.side_effect = RuntimeError("search down")

    result = warm_cache_after_onboarding(
        "user-aarav",
        packet,
        search=failing_search,
    )

    assert result.ok is False
    assert "search down" in (result.reason or "")


def test_onboarding_confirm_succeeds_when_warm_cache_fails(monkeypatch) -> None:
    clear_stack_state()
    event = sample_onboarding_confirm_event(with_gap_snapshot=False)

    def _fail_warm_cache(*_args, **_kwargs):
        from app.services.recommendation.warm_cache import WarmCacheResult

        return WarmCacheResult(ok=False, reason="forced failure")

    monkeypatch.setattr(
        "app.services.recommendation.onboarding_hook.warm_cache_after_onboarding",
        _fail_warm_cache,
    )

    result = on_onboarding_confirmed(event)

    assert "coordinator" in result["visited"]
    assert result["warm_cache"]["ok"] is False
    assert result["warm_cache"]["reason"] == "forced failure"
