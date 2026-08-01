from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from app.core.celery_app import celery_app
from app.workers.prewarm import prewarm_stack_task
from app.workers.tier2_tasks import curate_tier2_background_task


def test_celery_app_configuration() -> None:
    assert celery_app.main == "trellis_worker"
    assert "app.workers.prewarm" in celery_app.conf.include
    assert "app.workers.tier2_tasks" in celery_app.conf.include


def test_prewarm_stack_task_eager_execution(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CELERY_TASK_ALWAYS_EAGER", "true")
    celery_app.conf.task_always_eager = True

    with patch("app.services.curation.stack_orchestration.refresh_stack") as mock_refresh:
        mock_stack = type("MockStack", (), {"id": "stack-prewarm-123"})()
        mock_refresh.return_value = mock_stack

        result = prewarm_stack_task.delay()
        assert result.get() == "stack-prewarm-123"
        mock_refresh.assert_called_once()


def test_tier2_curation_task_eager_execution(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CELERY_TASK_ALWAYS_EAGER", "true")
    celery_app.conf.task_always_eager = True

    with patch("app.services.curation.stack_orchestration.refresh_stack") as mock_refresh:
        mock_stack = type("MockStack", (), {"id": "stack-tier2-456"})()
        mock_refresh.return_value = mock_stack

        result = curate_tier2_background_task.delay("demo-user-aarav")
        output = result.get()
        assert output["status"] == "success"
        assert output["user_id"] == "demo-user-aarav"
        assert output["stack_id"] == "stack-tier2-456"
