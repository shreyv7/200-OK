"""Cache pre-warm script. Owner: Backend. milestones.md M8.

Refreshes the demo user's stack once using whatever LLM_PROVIDER/
SEARCH_PROVIDER are configured in the environment. Safe no-op locally
(defaults to fake providers) — run with real keys configured shortly
before a live demo so the first click isn't a cold cache.
"""

from __future__ import annotations

import logging

from app.core.config import get_settings
from app.core.db import SessionLocal
from app.core.di import get_llm_provider, get_search_provider
from app.services.curation import stack_orchestration

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("prewarm")


def main() -> None:
    settings = get_settings()
    llm_provider = get_llm_provider(settings)
    search_provider = get_search_provider(settings)

    session = SessionLocal()
    try:
        stack = stack_orchestration.refresh_stack(
            session, settings.demo_user_id, search_provider, llm_provider
        )
        logger.info("Pre-warm complete: stack=%s", stack.id if stack else None)
    finally:
        session.close()


if __name__ == "__main__":
    main()
