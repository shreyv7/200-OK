"""Growth Partner Match mock endpoint. Owner: Backend. F10 (prd.md, P2 mock only), milestones.md M8.

Hardcoded in-memory fixture list — no persistence value for a mock-only
P2 feature (matches the fallback_resources.py precedent from M4).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.di import get_current_user_id
from app.schemas.partner import PartnerProfile

router = APIRouter(tags=["partners"])

_FAKE_PARTNERS = [
    PartnerProfile(
        id="partner_1", name="Alex R.", stage="beginner", goal="Ship a first public project",
        matchReason="Same builder stage and execution bottleneck as you.",
    ),
    PartnerProfile(
        id="partner_2", name="Sam K.", stage="beginner", goal="Speak at a local meetup",
        matchReason="Working through the same confidence bottleneck.",
    ),
    PartnerProfile(
        id="partner_3", name="Jordan P.", stage="intermediate", goal="Build a consistency streak",
        matchReason="A stage ahead on the same growth path.",
    ),
    PartnerProfile(
        id="partner_4", name="Riley T.", stage="intermediate", goal="Grow a professional network",
        matchReason="Complementary bottleneck — could trade accountability.",
    ),
    PartnerProfile(
        id="partner_5", name="Morgan L.", stage="advanced", goal="Mentor early-stage builders",
        matchReason="Ahead on your identity path, open to mentoring.",
    ),
]


@router.get("/partners/matches", response_model=list[PartnerProfile])
def get_partner_matches(_user_id: str = Depends(get_current_user_id)) -> list[PartnerProfile]:
    return _FAKE_PARTNERS
