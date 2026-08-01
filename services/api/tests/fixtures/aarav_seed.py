"""Aarav 21-Day Seeded Evidence Fixture for AIA tests.

Consumes Backend Pydantic models (app.schemas.evidence and app.schemas.identity).
Persona: Aarav, 22, wants to become a confident public speaker and builder who ships projects.
"""

from datetime import datetime, timedelta, timezone
from typing import List

from app.schemas.evidence import EvidenceEvent
from app.schemas.identity import DeclaredSelf, IdentityAttribute, IdentityMarker


def get_aarav_declared_self() -> DeclaredSelf:
    """Returns initial confirmed DeclaredSelf Pydantic model for Aarav persona."""
    now = datetime.now(timezone.utc)
    return DeclaredSelf(
        id="decl_aarav_v1",
        userId="aarav_demo",
        version=1,
        createdAt=now - timedelta(days=21),
        confirmedAt=now - timedelta(days=21),
        attributes=[
            IdentityAttribute(
                id="public_speaker",
                label="Public Speaker",
                weight=0.5,
                targetWeeklyPoints=15.0,
                markers=[
                    IdentityMarker(id="m_speak_1", label="Record speaking practice", description="60s talk run-through"),
                    IdentityMarker(id="m_speak_2", label="Attend speaking meetup", description="Toastmasters check-in"),
                ],
            ),
            IdentityAttribute(
                id="builder",
                label="Builder Who Ships",
                weight=0.5,
                targetWeeklyPoints=15.0,
                markers=[
                    IdentityMarker(id="m_build_1", label="GitHub Commit", description="Pushes working code"),
                    IdentityMarker(id="m_build_2", label="Publish Project", description="Publishes live link"),
                ],
            ),
        ],
    )


def generate_aarav_seed_events(ref_time: datetime = datetime.now(timezone.utc)) -> List[EvidenceEvent]:
    """Generates reproducible 21-day simulated EvidenceEvent Pydantic instances for Aarav."""
    events: List[EvidenceEvent] = []

    def make_evt(eid: str, etype: str, cat: str, attrs: List[str], days_ago: float, base_w: float, val: float, title: str) -> EvidenceEvent:
        ts = ref_time - timedelta(days=days_ago)
        return EvidenceEvent(
            id=eid,
            userId="aarav_demo",
            timestamp=ts,
            source="trellis",
            type=etype,
            category=cat,
            identityAttributeIds=attrs,
            baseWeight=base_w,
            value=val,
            simulated=True,
            metadata={"title": title},
        )

    # Week 3 (Days 14-20) - Passive heavy start
    events.extend([
        make_evt("evt_01", "passive_item", "passive_learning", ["public_speaker"], 20.0, 1.0, 1.0, "Watched 20min speech analysis video"),
        make_evt("evt_02", "passive_item", "passive_learning", ["builder"], 19.0, 1.0, 1.0, "Watched Next.js tutorial"),
        make_evt("evt_03", "focus_drift_10min", "focus_drift", ["builder"], 18.0, -2.0, -2.0, "Doomscroll shortform videos"),
        make_evt("evt_04", "focus_drift_10min", "focus_drift", ["builder"], 18.0, -2.0, -2.0, "Doomscroll shortform videos"),
        make_evt("evt_05", "passive_item", "passive_learning", ["public_speaker"], 17.0, 1.0, 1.0, "Read article on body language"),
        make_evt("evt_06", "passive_item", "passive_learning", ["builder"], 16.0, 1.0, 1.0, "Watched FastAPI crash course"),
        make_evt("evt_07", "focus_drift_10min", "focus_drift", ["public_speaker"], 15.0, -2.0, -2.0, "Memes scroll during focus window"),
        make_evt("evt_08", "passive_item", "passive_learning", ["builder"], 14.0, 1.0, 1.0, "Read React documentation"),
    ])

    # Week 2 (Days 7-13) - Mixed, first small creation
    events.extend([
        make_evt("evt_09", "passive_item", "passive_learning", ["public_speaker"], 13.0, 1.0, 1.0, "Watched TED talk"),
        make_evt("evt_10", "github_commit", "creation", ["builder"], 12.0, 4.0, 4.0, "Init repo commit"),
        make_evt("evt_11", "focus_drift_10min", "focus_drift", ["builder"], 12.0, -2.0, -2.0, "Social media scroll"),
        make_evt("evt_12", "passive_item", "passive_learning", ["builder"], 11.0, 1.0, 1.0, "Read Python async guide"),
        make_evt("evt_13", "focus_drift_10min", "focus_drift", ["public_speaker"], 10.0, -2.0, -2.0, "Shorts scroll"),
        make_evt("evt_14", "passive_item", "passive_learning", ["public_speaker"], 9.0, 1.0, 1.0, "Watched vocal warmups video"),
        make_evt("evt_15", "focus_drift_10min", "focus_drift", ["builder"], 8.0, -2.0, -2.0, "Feed scroll"),
        make_evt("evt_16", "passive_item", "passive_learning", ["builder"], 7.0, 1.0, 1.0, "Watched Docker tutorial"),
    ])

    # Week 1 (Days 0-6) - Recent events
    events.extend([
        make_evt("evt_17", "passive_item", "passive_learning", ["public_speaker"], 6.0, 1.0, 1.0, "Watched debate techniques"),
        make_evt("evt_18", "focus_drift_10min", "focus_drift", ["builder"], 5.0, -2.0, -2.0, "Reels doomscroll"),
        make_evt("evt_19", "focus_drift_10min", "focus_drift", ["builder"], 5.0, -2.0, -2.0, "Reels doomscroll"),
        make_evt("evt_20", "mission_completed", "creation", ["public_speaker"], 4.0, 3.0, 3.0, "Wrote 2-min talk outline"),
        make_evt("evt_21", "passive_item", "passive_learning", ["builder"], 4.0, 1.0, 1.0, "Read LangChain docs"),
        make_evt("evt_22", "focus_drift_10min", "focus_drift", ["public_speaker"], 3.0, -2.0, -2.0, "Feed scroll"),
        make_evt("evt_23", "github_commit", "creation", ["builder"], 2.0, 4.0, 4.0, "Add scoring module"),
        make_evt("evt_24", "passive_item", "passive_learning", ["public_speaker"], 1.0, 1.0, 1.0, "Watched storytelling video"),
        make_evt("evt_25", "focus_drift_10min", "focus_drift", ["builder"], 0.5, -2.0, -2.0, "Doomscroll 10min"),
        make_evt("evt_26", "passive_item", "passive_learning", ["builder"], 0.1, 1.0, 1.0, "Read API specs"),
    ])

    return events
