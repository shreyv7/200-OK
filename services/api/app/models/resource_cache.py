"""Resource cache table. Owner: Backend. milestones.md M4.

Caches search results by query hash so repeated refreshes for the same
query return a "Cached web" badge instead of re-hitting Tavily.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ResourceCacheModel(Base):
    __tablename__ = "resource_cache"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    query_hash: Mapped[str] = mapped_column(String, index=True)
    title: Mapped[str] = mapped_column(String)
    url: Mapped[str] = mapped_column(String)
    extract: Mapped[str] = mapped_column(String)
    source: Mapped[str] = mapped_column(String)
    badge: Mapped[str] = mapped_column(String)  # SourceBadge at fetch time
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
