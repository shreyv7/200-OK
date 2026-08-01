"""Tier-2 background curation tasks. Owner: Backend (Task C4).

Offloads heavy Tavily/YouTube retrieval and continuous curation off the main
request path into Celery background workers with automatic retries and backoff.
"""

from __future__ import annotations

import logging
from typing import Any

from app.core.celery_app import celery_app
from app.core.config import get_settings
from app.core.db import SessionLocal
from app.core.di import get_llm_provider, get_search_provider
from app.services.curation import stack_orchestration

logger = logging.getLogger("tier2_tasks")


@celery_app.task(bind=True, max_retries=3, default_retry_delay=5)
def curate_tier2_background_task(self: Any, user_id: str | None = None) -> dict[str, Any]:
    """Execute Tier-2 off-request-path deep curation in Celery worker."""
    if not user_id:
        raise ValueError("curate_tier2_background_task requires user_id (never demo fallback)")

    settings = get_settings()
    target_user_id = user_id
    llm_provider = get_llm_provider(settings)
    search_provider = get_search_provider(settings)

    session = SessionLocal()
    try:
        stack = stack_orchestration.refresh_stack(
            session, target_user_id, search_provider, llm_provider
        )
        stack_id = stack.id if stack else None
        logger.info("Tier-2 curation complete for user=%s stack=%s", target_user_id, stack_id)
        return {"status": "success", "user_id": target_user_id, "stack_id": stack_id}
    except Exception as exc:
        logger.error("Tier-2 curation failed for user=%s: %s", target_user_id, exc)
        raise self.retry(exc=exc)
    finally:
        session.close()
