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
from app.repositories import twin_repository
from app.schemas.evidence import RawMCPPayload
from app.schemas.identity import DeclaredSelf, IdentityAttribute, IdentityMarker
from app.services.evidence import service as evidence_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed")

SEED_RNG = 20260801  # fixed seed: identical demo data every run
DAYS = 21

# Fixture Declared Self for the demo persona (prd.md §4). NOT a substitute
# for the real Mirror Interview (M3) — this exists only so M2's dashboard
# and Gap math have a confirmed identity to compute against before
# onboarding ships. Attribute ids intentionally match AIA's
# KEYWORD_ATTRIBUTE_MAP (app/services/identity/enrichment.py) so seeded
# events enrich against real attributes instead of the "first attribute"
# fallback.
_DECLARED_ATTRIBUTES = [
    IdentityAttribute(
        id="public_speaker",
        label="Confident Public Speaker",
        weight=0.5,
        targetWeeklyPoints=15.0,
        markers=[
            IdentityMarker(id="speaks_publicly", label="Speaks in front of others"),
            IdentityMarker(id="publishes_recordings", label="Publishes recordings"),
        ],
    ),
    IdentityAttribute(
        id="builder",
        label="Builder Who Ships Projects",
        weight=0.5,
        targetWeeklyPoints=15.0,
        markers=[
            IdentityMarker(id="ships_code", label="Commits and publishes code"),
            IdentityMarker(id="completes_missions", label="Completes micro-missions"),
        ],
    ),
]

_trellis_adapter = FixtureTrellisAdapter()
_github_adapter = FixtureGithubAdapter()

# Per day, weighted toward passive/drift with sparse creation, matching
# Aarav's persona (prd.md §4: tutorials watched, nothing published).
_DAY_EVENT_TYPES = (
    ["passive_item"] * 2
    + ["focus_drift_10min"]
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


def _upsert_confirmed_twin(session, user_id: str) -> DeclaredSelf:
    existing = twin_repository.get_active_declared_self(session, user_id)
    if existing is not None:
        return existing
    return twin_repository.create_version(
        session,
        user_id=user_id,
        version=1,
        attributes=_DECLARED_ATTRIBUTES,
        confirmed_at=datetime.utcnow(),
    )


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
        twin = _upsert_confirmed_twin(session, user.id)
        inserted = _generate_history(session, user.id)
        logger.info(
            "Seed complete: user=%s twin_version=%d inserted_events=%d",
            user.id,
            twin.version,
            inserted,
        )
    finally:
        session.close()


if __name__ == "__main__":
    main()
