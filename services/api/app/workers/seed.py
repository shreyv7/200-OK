"""Seed script. Owner: Backend.

Generates the demo user + 21-day simulated Aarav history (F2, prd.md §4/§9).
Deterministic (fixed RNG seed) so every demo run is identical. Every event
is inserted through `evidence_service.ingest()` — never a raw bulk insert —
so the seeded history exercises the same pipeline as live/simulator events.
"""

from __future__ import annotations

import logging
import random
from datetime import datetime, timedelta

from app.core.config import get_settings
from app.core.db import SessionLocal
from app.integrations.mcp.github.adapter import FixtureGithubAdapter
from app.integrations.mcp.trellis.adapter import FixtureTrellisAdapter
from app.models.user import User
from app.schemas.evidence import RawMCPPayload
from app.services.evidence import service as evidence_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed")

SEED_RNG = 20260801  # fixed seed: identical demo data every run
DAYS = 21

_trellis_adapter = FixtureTrellisAdapter()
_github_adapter = FixtureGithubAdapter()

# Per day, weighted toward passive/drift with sparse creation, matching
# Aarav's persona (prd.md §4: tutorials watched, nothing published).
_DAY_EVENT_TYPES = (
    ["passive_item_completed"] * 2
    + ["focus_drift"]
    + ["mission_completed"]  # roughly every ~3rd day effectively via RNG below
)


def _upsert_demo_user(session) -> User:
    settings = get_settings()
    user = session.get(User, settings.demo_user_id)
    if user is None:
        user = User(id=settings.demo_user_id, capacity=100.0)
        session.add(user)
        session.commit()
        session.refresh(user)
    return user


def _generate_history(session, user_id: str) -> int:
    rng = random.Random(SEED_RNG)
    # Anchor to midnight UTC (not the exact current instant) so re-running the
    # script the same day reproduces identical timestamps and therefore
    # identical dedupe hashes — true idempotency, not just "close enough".
    now = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    inserted = 0

    for day_offset in range(DAYS, 0, -1):
        day = now - timedelta(days=day_offset)
        event_count = rng.randint(2, 4)

        for i in range(event_count):
            event_type = rng.choice(_DAY_EVENT_TYPES)
            timestamp = day + timedelta(hours=rng.randint(8, 22), minutes=i * 7)

            if event_type == "mission_completed" and rng.random() < 0.3:
                raw = RawMCPPayload(
                    sourceProvider="github",
                    rawPayload={
                        "userId": user_id,
                        "timestamp": timestamp.isoformat(),
                        "sha": f"seed-{day_offset}-{i}",
                        "message": "seeded commit",
                    },
                )
                event = _github_adapter.normalize(raw)
            else:
                raw = RawMCPPayload(
                    sourceProvider="trellis",
                    rawPayload={
                        "userId": user_id,
                        "type": event_type,
                        "timestamp": timestamp.isoformat(),
                        "units": 1.0,
                        "metadata": {"seeded_day_offset": day_offset},
                    },
                )
                event = _trellis_adapter.normalize(raw)

            ingest_request = evidence_service.request_from_event(event)
            _row, created = evidence_service.ingest(session, ingest_request)
            if created:
                inserted += 1

    return inserted


def main() -> None:
    session = SessionLocal()
    try:
        user = _upsert_demo_user(session)
        inserted = _generate_history(session, user.id)
        logger.info("Seed complete: user=%s inserted_events=%d", user.id, inserted)
    finally:
        session.close()


if __name__ == "__main__":
    main()
