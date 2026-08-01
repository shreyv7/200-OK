"""Cache -> live search -> seeded fallback chain. Owner: Backend. milestones.md M4.

Implements prd.md §8 retrieval fallback logic exactly:
1. Fresh cache hit -> "Cached web".
2. Otherwise call the SearchProvider under a hard timeout -> "Live web",
   persisting successful results to cache.
3. On timeout, quota exhaustion, malformed results, or any failure ->
   seeded fallback set -> "Curated fallback".
Retrieval failure must never raise or return an empty list — always
falls through to the seeded set (F4/F5 acceptance: never blocks the
feed morph, never an empty intervention).
"""

from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy.orm import Session

from app.providers.search.base import Document, SearchProvider
from app.repositories import resource_cache_repository

SeededFallback = Callable[[str], list[Document]]


def search_with_fallback(
    db: Session,
    query: str,
    search_provider: SearchProvider,
    seeded_fallback: SeededFallback,
    timeout_seconds: float = 1.5,
) -> tuple[list[Document], str]:
    """Returns (documents, source_badge). Never raises, never returns []."""
    cached = resource_cache_repository.get_fresh(db, query)
    if cached:
        return cached, "Cached web"

    # Not a `with` block: a hung/slow provider must not block this call
    # past `timeout_seconds` — the context manager's __exit__ would call
    # shutdown(wait=True) and block until the orphaned thread finishes,
    # defeating the timeout entirely.
    executor = ThreadPoolExecutor(max_workers=1)
    try:
        future = executor.submit(search_provider.search, query)
        documents = future.result(timeout=timeout_seconds)

        valid = [d for d in documents if d.title and d.url and d.extract]
        if valid:
            resource_cache_repository.store(db, query, valid, badge="Live web")
            return valid, "Live web"
    except Exception:
        # Timeout, quota exhaustion, malformed results, network failure —
        # all treated identically: fall through to the seeded fallback.
        pass
    finally:
        executor.shutdown(wait=False, cancel_futures=True)

    return seeded_fallback(query), "Curated fallback"
