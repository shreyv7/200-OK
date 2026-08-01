"""Trigger-driven Tier-2 stack refresh (work.md C5).

Enqueues Celery curation for the authenticated user only — never falls back
to demo-user-aarav from API call sites.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def enqueue_tier2_stack_refresh(user_id: str) -> None:
    """Fire-and-forget Tier-2 refresh. Requires authenticated user_id (A/D)."""
    if not user_id:
        raise ValueError("enqueue_tier2_stack_refresh requires authenticated user_id")

    from app.workers.tier2_tasks import curate_tier2_background_task

    try:
        curate_tier2_background_task.delay(user_id)
    except Exception as exc:  # noqa: BLE001 — never fail the Tier-0/1 request path
        logger.warning("Failed to enqueue Tier-2 refresh for %s: %s", user_id, exc)
