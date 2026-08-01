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
from app.providers.llm.fake import FakeLLMProvider
from app.providers.search.fake import FakeSearchProvider
from app.repositories import evolution_repository, intervention_repository, ledger_repository, twin_repository
from app.schemas.evidence import RawMCPPayload
from app.schemas.identity import DeclaredSelf, IdentityAttribute, IdentityMarker
from app.services.curation import stack_orchestration
from app.services.evidence import service as evidence_service
from app.workers.seed_catalog import seed_catalog

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


def _ensure_prepared_intervention(session, user_id: str) -> bool:
    """At least one cached stack must exist so `GET /stack/active` never
    404s on a fresh demo environment (milestones.md M4). Uses Fake
    providers — seed data must be deterministic, never a live network
    call, matching the rest of this script's philosophy."""
    if intervention_repository.get_active(session, user_id) is not None:
        return False
    stack_orchestration.refresh_stack(
        session, user_id, search_provider=FakeSearchProvider(), llm_provider=FakeLLMProvider()
    )
    return True


DEMO_HYPOTHESIS_FAMILY = "media_public_speaking"


def _ensure_demo_dismissal_history(session, user_id: str) -> int:
    """Seeds two prior dismissals (prd.md F7 demo script: the third LIVE
    dismissal on stage crosses DISMISSAL_FAILURE_THRESHOLD=3). Idempotent —
    only inserts if this family has no dismissal history yet."""
    existing = ledger_repository.count_recent_dismissals(session, DEMO_HYPOTHESIS_FAMILY, 14)
    if existing > 0:
        return 0

    active = intervention_repository.get_active(session, user_id)
    hypothesis_id = active.hypothesis_id if active is not None else f"hyp-{user_id}"

    for days_ago in (5, 3):
        ledger_repository.record(
            session,
            user_id=user_id,
            hypothesis_id=hypothesis_id,
            hypothesis_family=DEMO_HYPOTHESIS_FAMILY,
            action="dismissed",
            verdict="pending",
            timestamp=datetime.utcnow() - timedelta(days=days_ago),
        )
    return 2


def _ensure_demo_evolution_proposal(session, user_id: str) -> bool:
    """Seeds one evolution proposal (prd.md F11 MVP: no live LLM call needed
    for the demo to have something to accept/reject)."""
    if evolution_repository.has_pending_for_user(session, user_id):
        return False
    evolution_repository.create(
        session,
        user_id=user_id,
        proposed_attributes=_DECLARED_ATTRIBUTES
        + [
            IdentityAttribute(
                id="entrepreneur",
                label="Startup Founder",
                weight=0.3,
                targetWeeklyPoints=15.0,
                markers=[IdentityMarker(id="ships_product", label="Ships a product update")],
            )
        ],
        cited_evidence_ids=[],
        rationale=(
            "You originally wanted to become a public speaker, but your recent "
            "behavior suggests a growing interest in entrepreneurship."
        ),
    )
    return True


def main() -> None:
    session = SessionLocal()
    try:
        user = _upsert_demo_user(session)
        twin = _upsert_confirmed_twin(session, user.id)
        inserted = _generate_history(session, user.id)
        prepared = _ensure_prepared_intervention(session, user.id)
        dismissals = _ensure_demo_dismissal_history(session, user.id)
        stories, tools, mentors = seed_catalog(session)
        evolution_seeded = _ensure_demo_evolution_proposal(session, user.id)
        logger.info(
            "Seed complete: user=%s twin_version=%d inserted_events=%d "
            "prepared_stack=%s seeded_dismissals=%d catalog=%d/%d/%d evolution=%s",
            user.id,
            twin.version,
            inserted,
            prepared,
            dismissals,
            stories,
            tools,
            mentors,
            evolution_seeded,
        )
    finally:
        session.close()


if __name__ == "__main__":
    main()
