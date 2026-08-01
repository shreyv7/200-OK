"""Aarav 21-Day Seeded Evidence Fixture for AIA tests.

Persona: Aarav, 22, wants to become a confident public speaker and builder who ships projects.
Screen time / history: 2.5 hrs/day short-form video, tutorials watched, low creation.
"""

from typing import List
from app.services.identity.sanitizer import SanitizedEvent
from app.services.identity.scoring.declared_self import DeclaredSelf


def get_aarav_declared_self() -> DeclaredSelf:
    """Returns initial confirmed DeclaredSelf for Aarav persona."""
    return {
        "version": 1,
        "user_id": "aarav_demo",
        "confirmed": True,
        "created_at": "2026-07-11T00:00:00Z",
        "attributes": [
            {
                "id": "public_speaker",
                "label": "Public Speaker",
                "description": "Speaks in front of audiences, publishes talks, practices delivery",
                "weight": 0.5,
                "declared_weekly_target": 15.0,
                "markers": [
                    {
                        "id": "m_speak_1",
                        "label": "Record speaking practice",
                        "description": "Records 60-second talk run-through",
                        "observable_examples": ["60s recording"],
                    },
                    {
                        "id": "m_speak_2",
                        "label": "Attend speaking meetup",
                        "description": "Attends Toastmasters or presentation workshop",
                        "observable_examples": ["Event check-in"],
                    },
                ],
            },
            {
                "id": "builder",
                "label": "Builder Who Ships",
                "description": "Commits code regularly, publishes open source projects, builds tools",
                "weight": 0.5,
                "declared_weekly_target": 15.0,
                "markers": [
                    {
                        "id": "m_build_1",
                        "label": "GitHub Commit",
                        "description": "Pushes working code to repo",
                        "observable_examples": ["git commit"],
                    },
                    {
                        "id": "m_build_2",
                        "label": "Publish Project",
                        "description": "Publishes demo or blog post",
                        "observable_examples": ["Live link"],
                    },
                ],
            },
        ],
    }


def generate_aarav_seed_events() -> List[SanitizedEvent]:
    """Generates reproducible 21-day simulated evidence events for Aarav (30 events total).
    
    Composition: ~60% passive learning, ~25% focus drift, ~15% creation.
    """
    events: List[SanitizedEvent] = []
    
    # 21-day window relative delta_days (0 = today, 20 = 20 days ago)
    # Week 3 (Days 14-20) - Passive heavy start
    events.extend([
        SanitizedEvent("evt_01", "aarav_demo", "passive_item", "public_speaker", 1.0, delta_days=20.0, simulated=True, metadata={"title": "Watched 20min speech analysis video"}),
        SanitizedEvent("evt_02", "aarav_demo", "passive_item", "builder", 1.0, delta_days=19.0, simulated=True, metadata={"title": "Watched Next.js tutorial"}),
        SanitizedEvent("evt_03", "aarav_demo", "focus_drift_10min", "builder", 1.0, delta_days=18.0, simulated=True, metadata={"title": "Doomscroll shortform videos"}),
        SanitizedEvent("evt_04", "aarav_demo", "focus_drift_10min", "builder", 1.0, delta_days=18.0, simulated=True, metadata={"title": "Doomscroll shortform videos"}),
        SanitizedEvent("evt_05", "aarav_demo", "passive_item", "public_speaker", 1.0, delta_days=17.0, simulated=True, metadata={"title": "Read article on body language"}),
        SanitizedEvent("evt_06", "aarav_demo", "passive_item", "builder", 1.0, delta_days=16.0, simulated=True, metadata={"title": "Watched FastAPI crash course"}),
        SanitizedEvent("evt_07", "aarav_demo", "focus_drift_10min", "public_speaker", 1.0, delta_days=15.0, simulated=True, metadata={"title": "Memes scroll during focus window"}),
        SanitizedEvent("evt_08", "aarav_demo", "passive_item", "builder", 1.0, delta_days=14.0, simulated=True, metadata={"title": "Read React documentation"}),
    ])

    # Week 2 (Days 7-13) - Mixed, first small creation
    events.extend([
        SanitizedEvent("evt_09", "aarav_demo", "passive_item", "public_speaker", 1.0, delta_days=13.0, simulated=True, metadata={"title": "Watched TED talk"}),
        SanitizedEvent("evt_10", "aarav_demo", "github_commit", "builder", 1.0, delta_days=12.0, simulated=True, metadata={"title": "Init repo commit"}),  # +4.0
        SanitizedEvent("evt_11", "aarav_demo", "focus_drift_10min", "builder", 1.0, delta_days=12.0, simulated=True, metadata={"title": "Social media scroll"}),
        SanitizedEvent("evt_12", "aarav_demo", "passive_item", "builder", 1.0, delta_days=11.0, simulated=True, metadata={"title": "Read Python async guide"}),
        SanitizedEvent("evt_13", "aarav_demo", "focus_drift_10min", "public_speaker", 1.0, delta_days=10.0, simulated=True, metadata={"title": "Shorts scroll"}),
        SanitizedEvent("evt_14", "aarav_demo", "passive_item", "public_speaker", 1.0, delta_days=9.0, simulated=True, metadata={"title": "Watched vocal warmups video"}),
        SanitizedEvent("evt_15", "aarav_demo", "focus_drift_10min", "builder", 1.0, delta_days=8.0, simulated=True, metadata={"title": "Feed scroll"}),
        SanitizedEvent("evt_16", "aarav_demo", "passive_item", "builder", 1.0, delta_days=7.0, simulated=True, metadata={"title": "Watched Docker tutorial"}),
    ])

    # Week 1 (Days 0-6) - Recent events leading to current state
    events.extend([
        SanitizedEvent("evt_17", "aarav_demo", "passive_item", "public_speaker", 1.0, delta_days=6.0, simulated=True, metadata={"title": "Watched debate techniques"}),
        SanitizedEvent("evt_18", "aarav_demo", "focus_drift_10min", "builder", 1.0, delta_days=5.0, simulated=True, metadata={"title": "Reels doomscroll"}),
        SanitizedEvent("evt_19", "aarav_demo", "focus_drift_10min", "builder", 1.0, delta_days=5.0, simulated=True, metadata={"title": "Reels doomscroll"}),
        SanitizedEvent("evt_20", "aarav_demo", "mission_completed", "public_speaker", 1.0, delta_days=4.0, simulated=True, metadata={"title": "Wrote 2-min talk outline"}),  # +3.0
        SanitizedEvent("evt_21", "aarav_demo", "passive_item", "builder", 1.0, delta_days=4.0, simulated=True, metadata={"title": "Read LangChain docs"}),
        SanitizedEvent("evt_22", "aarav_demo", "focus_drift_10min", "public_speaker", 1.0, delta_days=3.0, simulated=True, metadata={"title": "Feed scroll"}),
        SanitizedEvent("evt_23", "aarav_demo", "github_commit", "builder", 1.0, delta_days=2.0, simulated=True, metadata={"title": "Add scoring module"}),  # +4.0
        SanitizedEvent("evt_24", "aarav_demo", "passive_item", "public_speaker", 1.0, delta_days=1.0, simulated=True, metadata={"title": "Watched storytelling video"}),
        SanitizedEvent("evt_25", "aarav_demo", "focus_drift_10min", "builder", 1.0, delta_days=0.5, simulated=True, metadata={"title": "Doomscroll 10min"}),
        SanitizedEvent("evt_26", "aarav_demo", "passive_item", "builder", 1.0, delta_days=0.1, simulated=True, metadata={"title": "Read API specs"}),
    ])

    return events
