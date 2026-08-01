from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from app.services.identity import orchestration
from tests.conftest import ensure_user


def test_recompute_and_persist_passes_llm_to_user_gap(db_session) -> None:
    from app.repositories import twin_repository
    from app.workers.seed import _DECLARED_ATTRIBUTES

    user_id = "user-bottleneck-llm"
    ensure_user(db_session, user_id)
    if twin_repository.get_active_declared_self(db_session, user_id) is None:
        twin_repository.create_version(
            db_session,
            user_id=user_id,
            version=1,
            attributes=_DECLARED_ATTRIBUTES,
            confirmed_at=datetime.now(timezone.utc),
        )

    fake_llm = MagicMock()
    with patch(
        "app.services.identity.orchestration.recompute_user_gap",
        side_effect=RuntimeError("stop-after-llm-assert"),
    ) as mock_recompute:
        try:
            orchestration.recompute_and_persist(db_session, user_id, llm_provider=fake_llm)
        except RuntimeError as exc:
            assert "stop-after-llm-assert" in str(exc)

    assert mock_recompute.called
    assert mock_recompute.call_args.kwargs.get("llm_provider") is fake_llm


def test_refresh_stack_threads_llm_into_recompute(db_session) -> None:
    from app.core.config import get_settings
    from app.core.di import get_llm_provider, get_search_provider
    from app.services.curation import stack_orchestration

    settings = get_settings()
    llm = get_llm_provider(settings)
    search = get_search_provider(settings)

    with patch(
        "app.services.curation.stack_orchestration.orchestration.recompute_and_persist"
    ) as mock_recompute:
        mock_recompute.return_value = None
        stack_orchestration.refresh_stack(db_session, "missing-user", search, llm)

    mock_recompute.assert_called_once()
    assert mock_recompute.call_args.kwargs.get("llm_provider") is llm
