from __future__ import annotations

from app.services.recommendation import onboarding_hook


def test_only_emit_onboarding_confirmed_is_public_confirm_entrypoint() -> None:
    """AIS must not react to draft interview turns — only explicit confirm emit."""
    assert hasattr(onboarding_hook, "emit_onboarding_confirmed")
    assert hasattr(onboarding_hook, "on_onboarding_confirmed")
    assert hasattr(onboarding_hook, "register_onboarding_confirm_handler")
    assert not hasattr(onboarding_hook, "on_interview_turn")
    assert not hasattr(onboarding_hook, "on_draft_extraction")
