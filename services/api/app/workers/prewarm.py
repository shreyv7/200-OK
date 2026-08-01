"""Cache pre-warm script. Owner: Backend. milestones.md M8.

Refreshes the demo user's stack once using whatever LLM_PROVIDER/
SEARCH_PROVIDER are configured in the environment. Safe no-op locally
(defaults to fake providers) — run with real keys configured shortly
before a live demo so the first click isn't a cold cache.
"""

from __future__ import annotations

import logging

from app.core.celery_app import celery_app
from app.core.config import get_settings
from app.core.db import SessionLocal
from app.core.di import get_llm_provider, get_search_provider
from app.services.curation import stack_orchestration

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("prewarm")


@celery_app.task(bind=True, max_retries=3, default_retry_delay=5)
def prewarm_stack_task(self: Any | None = None) -> str | None:
    """Celery task to pre-warm the demo user's identity stack."""
    settings = get_settings()
    llm_provider = get_llm_provider(settings)
    search_provider = get_search_provider(settings)

    session = SessionLocal()
    try:
        stack = stack_orchestration.refresh_stack(
            session, settings.demo_user_id, search_provider, llm_provider
        )
        stack_id = stack.id if stack else None
        logger.info("Pre-warm complete: stack=%s", stack_id)
        return stack_id
    except Exception as exc:
        logger.error("Pre-warm task failed: %s", exc)
        if self is not None and hasattr(self, "retry"):
            raise self.retry(exc=exc)
        raise
    finally:
        session.close()


def main() -> None:
    prewarm_stack_task()


if __name__ == "__main__":
    main()

