"""Dependency-injection surface. Owner: Backend.

Central place other modules import `Depends(...)` wiring from, per
techstack.md §5.4 (DB sessions, current user, repositories, providers).
"""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import get_current_user_id

__all__ = ["get_db", "get_current_user_id", "Depends", "Session"]
