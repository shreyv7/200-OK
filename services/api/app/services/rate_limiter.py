"""Redis-backed per-user rate limiter. Owner: Backend (Task C6).

Protects evidence ingest and LLM/Curator-triggering endpoints against burst POSTs.
Isolated per user_id — throttling user A never affects user B.
Includes local in-memory sliding window fallback for environments without Redis.
"""

from __future__ import annotations

import time
from collections import defaultdict
from typing import Any

from fastapi import HTTPException, status

from app.core.config import get_settings

_in_memory_windows: dict[str, list[float]] = defaultdict(list)


def check_rate_limit(
    key_prefix: str,
    user_id: str,
    limit: int,
    window_seconds: int = 10,
    redis_client: Any | None = None,
) -> None:
    """Check rate limit for (key_prefix, user_id). Raises 429 if limit exceeded."""
    if not user_id:
        return

    key = f"rate_limit:{key_prefix}:{user_id}"
    now = time.time()

    if redis_client is not None:
        try:
            pipe = redis_client.pipeline()
            pipe.zremrangebyscore(key, 0, now - window_seconds)
            pipe.zadd(key, {str(now): now})
            pipe.zcard(key)
            pipe.expire(key, window_seconds)
            results = pipe.execute()
            count = results[2]
            if count > limit:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded ({limit} requests per {window_seconds}s).",
                )
            return
        except HTTPException:
            raise
        except Exception:
            # Fall through to in-memory sliding window
            pass

    # In-memory sliding window fallback
    timestamps = _in_memory_windows[key]
    cutoff = now - window_seconds
    _in_memory_windows[key] = [t for t in timestamps if t > cutoff]
    _in_memory_windows[key].append(now)

    if len(_in_memory_windows[key]) > limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded ({limit} requests per {window_seconds}s).",
        )


def reset_rate_limits() -> None:
    """Utility for testing."""
    _in_memory_windows.clear()
