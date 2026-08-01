"""Growth Partner Match card — embedding similarity over fake profiles (P2) — AIS M8."""

from __future__ import annotations

import math
from dataclasses import dataclass

from app.providers.embeddings import EmbeddingProvider
from app.providers.embeddings import FakeEmbeddingProvider


@dataclass(frozen=True)
class PartnerProfile:
    id: str
    display_name: str
    stage: str
    goal: str
    bottleneck: str
    bio: str


@dataclass(frozen=True)
class PartnerMatchCard:
    profile_id: str
    display_name: str
    similarity: float
    proposed_check_in: str
    source_badge: str = "Simulated prototype"
    rationale: str = ""


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left)) or 1.0
    right_norm = math.sqrt(sum(b * b for b in right)) or 1.0
    return dot / (left_norm * right_norm)


def _profile_text(profile: PartnerProfile) -> str:
    return f"{profile.stage} {profile.goal} {profile.bottleneck} {profile.bio}"


def _user_text(user_profile: dict[str, str]) -> str:
    return " ".join(
        str(user_profile.get(key, ""))
        for key in ("stage", "goal", "bottleneck", "summary")
    )


def match_partner(
    user_profile: dict[str, str],
    candidates: list[PartnerProfile],
    *,
    embedder: EmbeddingProvider | None = None,
) -> PartnerMatchCard | None:
    """Return the best stage/goal match — never popularity-based."""
    if not candidates:
        return None

    provider = embedder or FakeEmbeddingProvider()
    user_vector = provider.embed([_user_text(user_profile)])[0]
    scored: list[tuple[PartnerProfile, float]] = []
    for profile in candidates:
        vector = provider.embed([_profile_text(profile)])[0]
        similarity = _cosine_similarity(user_vector, vector)
        if profile.stage == user_profile.get("stage"):
            similarity += 0.05
        if profile.bottleneck == user_profile.get("bottleneck"):
            similarity += 0.05
        scored.append((profile, similarity))

    scored.sort(key=lambda item: (-item[1], item[0].id))
    best_profile, best_score = scored[0]
    return PartnerMatchCard(
        profile_id=best_profile.id,
        display_name=best_profile.display_name,
        similarity=round(best_score, 4),
        proposed_check_in="Weekly 15-minute accountability check-in",
        rationale=(
            f"Someone at your stage with a similar {best_profile.bottleneck} bottleneck "
            f"working toward {best_profile.goal}."
        ),
    )
