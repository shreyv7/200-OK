"""Cache pre-warm script. Owner: Backend. milestones.md M8 / A2.

Refreshes a specific user's stack using configured LLM/SEARCH providers.
Requires ``PREWARM_USER_ID`` — never defaults to demo-user-aarav.
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
    if not settings.prewarm_user_id:
        raise SystemExit(
            "Refusing to prewarm without PREWARM_USER_ID "
            "(set to a real users.id — never implied demo-user-aarav)."
        )

    llm_provider = get_llm_provider(settings)
    search_provider = get_search_provider(settings)

    session = SessionLocal()
    try:
        stack = stack_orchestration.refresh_stack(
            session, settings.prewarm_user_id, search_provider, llm_provider
        )
        logger.info("Pre-warm complete: user=%s stack=%s", settings.prewarm_user_id, stack.id if stack else None)
    finally:
        session.close()


if __name__ == "__main__":
    main()
