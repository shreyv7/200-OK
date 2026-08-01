"""Cache pre-warm script. Owner: Backend. milestones.md M8 / A2.

Refreshes a specific user's stack using configured LLM/SEARCH providers.
Requires ``PREWARM_USER_ID`` — never defaults to demo-user-aarav.
"""

from __future__ import annotations

import logging
from typing import Any

from app.core.celery_app import celery_app
from app.core.config import get_settings
from app.core.db import SessionLocal
from app.core.di import get_llm_provider, get_search_provider
from app.services.curation import stack_orchestration

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("prewarm")


@celery_app.task(bind=True, max_retries=3, default_retry_delay=5)
def prewarm_stack_task(self: Any, user_id: str | None = None) -> str | None:
    """Celery task to pre-warm a user's identity stack."""
    settings = get_settings()
    target_user_id = user_id or settings.prewarm_user_id
    if not target_user_id:
        raise ValueError(
            "Refusing to prewarm without PREWARM_USER_ID "
            "(set to a real users.id — never implied demo-user-aarav)."
        )

    llm_provider = get_llm_provider(settings)
    search_provider = get_search_provider(settings)

    session = SessionLocal()
    try:
        stack = stack_orchestration.refresh_stack(
            session, target_user_id, search_provider, llm_provider
        )
        stack_id = stack.id if stack else None
        logger.info("Pre-warm complete: user=%s stack=%s", target_user_id, stack_id)
        return stack_id
    except Exception as exc:
        logger.error("Pre-warm task failed: %s", exc)
        if self is not None and hasattr(self, "retry"):
            raise self.retry(exc=exc)
        raise
    finally:
        session.close()


def main() -> None:
    settings = get_settings()
    if not settings.prewarm_user_id:
        raise SystemExit(
            "Refusing to prewarm without PREWARM_USER_ID "
            "(set to a real users.id — never implied demo-user-aarav)."
        )
    prewarm_stack_task.delay(settings.prewarm_user_id)


if __name__ == "__main__":
    main()
