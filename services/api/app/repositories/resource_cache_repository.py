"""Resource cache persistence. Owner: Backend. milestones.md M4."""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.resource_cache import ResourceCacheModel
from app.providers.search.base import Document

DEFAULT_TTL = timedelta(hours=1)


def query_hash(query: str) -> str:
    return hashlib.sha256(query.strip().lower().encode("utf-8")).hexdigest()


def get_fresh(db: Session, query: str, ttl: timedelta = DEFAULT_TTL) -> list[Document] | None:
    """Return cached documents for `query` if any row is within `ttl`, else None."""
    cutoff = datetime.utcnow() - ttl
    stmt = (
        select(ResourceCacheModel)
        .where(ResourceCacheModel.query_hash == query_hash(query))
        .where(ResourceCacheModel.fetched_at >= cutoff)
    )
    rows = list(db.scalars(stmt))
    if not rows:
        return None
    return [
        Document(title=r.title, url=r.url, extract=r.extract, source=r.source)
        for r in rows
    ]


def store(db: Session, query: str, documents: list[Document], badge: str) -> None:
    qh = query_hash(query)
    for doc in documents:
        row = ResourceCacheModel(
            query_hash=qh,
            title=doc.title,
            url=doc.url,
            extract=doc.extract,
            source=doc.source,
            badge=badge,
        )
        db.add(row)
    db.commit()
