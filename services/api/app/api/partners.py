"""Growth Partner Match endpoint. Owner: Backend. F10 (prd.md).

Ranks the seeded partner pool against the caller's twin/bottleneck using
Qdrant vector similarity when VECTOR_DB_PROVIDER=qdrant, otherwise
deterministic local embeddings.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.di import get_current_user_id, get_db
from app.repositories import twin_repository
from app.schemas.partner import PartnerProfile
from app.services.identity import orchestration
from app.services.recommendation.partner_match import (
    PartnerProfile as MatchProfile,
    rank_partners,
)

router = APIRouter(tags=["partners"])

_CANDIDATE_POOL = [
    MatchProfile(
        id="partner_1",
        display_name="Alex R.",
        stage="beginner",
        goal="Ship a first public project",
        bottleneck="execution",
        bio="Shipping small public artifacts every week.",
    ),
    MatchProfile(
        id="partner_2",
        display_name="Sam K.",
        stage="beginner",
        goal="Speak at a local meetup",
        bottleneck="confidence",
        bio="Building confidence through short speaking reps.",
    ),
    MatchProfile(
        id="partner_3",
        display_name="Jordan P.",
        stage="intermediate",
        goal="Build a consistency streak",
        bottleneck="discipline",
        bio="Maintaining a daily build streak.",
    ),
    MatchProfile(
        id="partner_4",
        display_name="Riley T.",
        stage="intermediate",
        goal="Grow a professional network",
        bottleneck="networking",
        bio="Reaching out to one new builder weekly.",
    ),
    MatchProfile(
        id="partner_5",
        display_name="Morgan L.",
        stage="advanced",
        goal="Mentor early-stage builders",
        bottleneck="execution",
        bio="Ahead on the builder path, open to mentoring.",
    ),
]


def _user_profile(db: Session, user_id: str) -> dict[str, str]:
    bottleneck = "execution"
    stage = "beginner"
    goal = "grow consistently"
    summary = ""

    try:
        result = orchestration.recompute_and_persist(db, user_id)
        if result and result.bottleneck:
            bottleneck = result.bottleneck.bottleneck
    except Exception:
        # Endpoint must stay usable before onboarding / without a twin.
        pass

    try:
        declared = twin_repository.get_active_declared_self(db, user_id)
    except Exception:
        declared = None

    if declared and declared.attributes:
        labels = [a.label for a in declared.attributes]
        summary = "; ".join(labels[:4])
        total_weight = sum(a.weight for a in declared.attributes)
        if total_weight >= 2.5:
            stage = "advanced"
        elif total_weight >= 1.5:
            stage = "intermediate"
        goal = labels[0]

    return {
        "stage": stage,
        "goal": goal,
        "bottleneck": bottleneck,
        "summary": summary or f"{bottleneck} growth",
    }


@router.get("/partners/matches", response_model=list[PartnerProfile])
def get_partner_matches(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
) -> list[PartnerProfile]:
    user_profile = _user_profile(db, user_id)
    ranked = rank_partners(user_profile, _CANDIDATE_POOL, limit=5)
    return [
        PartnerProfile(
            id=card.profile_id,
            name=card.display_name,
            stage=card.stage,
            goal=card.goal,
            matchReason=card.rationale,
            similarity=card.similarity,
            sourceBadge=card.source_badge,
            prototype=card.source_badge == "Simulated prototype",
        )
        for card in ranked
    ]
