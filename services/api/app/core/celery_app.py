"""Celery application configuration. Owner: Backend (Task C4).

Configures Celery broker and result backend with Redis.
Includes support for eager execution mode in test environments.
"""

from __future__ import annotations

import os
from celery import Celery

from app.core.config import get_settings

settings = get_settings()

redis_broker = settings.redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "trellis_worker",
    broker=redis_broker,
    backend=redis_broker,
    include=[
        "app.workers.prewarm",
        "app.workers.tier2_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_always_eager=os.getenv("CELERY_TASK_ALWAYS_EAGER", "false").lower() == "true",
)
