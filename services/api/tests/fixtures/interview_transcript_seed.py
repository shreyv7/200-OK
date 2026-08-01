"""Sample Onboarding Transcript Fixture for AIA M3 tests.

Provides realistic 5-turn Mirror Interview transcript state for Aarav persona.
"""

from datetime import datetime, timedelta, timezone
from app.services.identity.confirmation import InterviewState, InterviewTurn


def get_sample_aarav_transcript() -> InterviewState:
    """Returns a complete 5-turn InterviewState for Aarav persona."""
    now = datetime.now(timezone.utc)
    turns = [
        InterviewTurn(1, "agent", "What primary identity or aspirational role do you want to build right now?", now - timedelta(minutes=10)),
        InterviewTurn(1, "user", "I want to become a confident public speaker and a software builder who ships open source projects.", now - timedelta(minutes=9)),
        InterviewTurn(2, "agent", "Why is achieving this identity milestone deeply important to you at this stage?", now - timedelta(minutes=8)),
        InterviewTurn(2, "user", "Because I want to lead tech teams, present at conferences, and build real tools that help people.", now - timedelta(minutes=7)),
        InterviewTurn(3, "agent", "What current daily habits or creation activities best reflect this identity?", now - timedelta(minutes=6)),
        InterviewTurn(3, "user", "I write speech outlines occasionally and push git commits to my GitHub repository.", now - timedelta(minutes=5)),
        InterviewTurn(4, "agent", "What is the single biggest blocker, distraction, or focus drift holding you back?", now - timedelta(minutes=4)),
        InterviewTurn(4, "user", "I spend too much time watching YouTube tutorials and doomscrolling shortform videos instead of shipping code.", now - timedelta(minutes=3)),
        InterviewTurn(5, "agent", "How many evidence points or hours per week can you realistically commit to this identity?", now - timedelta(minutes=2)),
        InterviewTurn(5, "user", "I can commit about 15 hours per week split evenly between speaking practice and building.", now - timedelta(minutes=1)),
    ]

    return InterviewState(
        userId="aarav_demo",
        currentTurn=5,
        maxTurns=5,
        transcript=turns,
        isComplete=True,
    )
