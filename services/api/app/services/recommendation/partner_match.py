"""Growth Partner Match — Qdrant vector similarity & profile matching."""

from __future__ import annotations

import math
from dataclasses import dataclass

from app.providers.embeddings import EmbeddingProvider, get_embedding_provider
from app.providers.qdrant import QdrantVectorStore, get_vector_store


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
    source_badge: str = "Qdrant Vector Match"
    rationale: str = ""
    stage: str = ""
    goal: str = ""


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


def _score_boost(profile: PartnerProfile, user_profile: dict[str, str], score: float) -> float:
    boosted = score
    if profile.stage == user_profile.get("stage"):
        boosted = min(1.0, boosted + 0.05)
    if profile.bottleneck == user_profile.get("bottleneck"):
        boosted = min(1.0, boosted + 0.05)
    return boosted


def _card_from_profile(
    profile: PartnerProfile,
    score: float,
    *,
    source_badge: str,
) -> PartnerMatchCard:
    return PartnerMatchCard(
        profile_id=profile.id,
        display_name=profile.display_name,
        similarity=round(score, 4),
        proposed_check_in="Weekly 15-minute accountability check-in",
        source_badge=source_badge,
        rationale=(
            f"Someone at your stage with a similar {profile.bottleneck} bottleneck "
            f"working toward {profile.goal}."
            if source_badge == "Simulated prototype"
            else (
                f"Qdrant vector matched builder at your stage with a similar "
                f"{profile.bottleneck} bottleneck working toward {profile.goal}."
            )
        ),
        stage=profile.stage,
        goal=profile.goal,
    )


def rank_partners(
    user_profile: dict[str, str],
    candidates: list[PartnerProfile],
    *,
    embedder: EmbeddingProvider | None = None,
    vector_store: QdrantVectorStore | None = None,
    limit: int = 5,
) -> list[PartnerMatchCard]:
    """Rank partner candidates via Qdrant when enabled, else local cosine."""
    if not candidates:
        return []

    provider = embedder or get_embedding_provider()
    user_vector = provider.embed([_user_text(user_profile)])[0]
    store = vector_store or get_vector_store()
    candidate_map = {p.id: p for p in candidates}

    ranked: list[PartnerMatchCard] = []
    seen: set[str] = set()

    if store.is_enabled:
        points = []
        for profile in candidates:
            vec = provider.embed([_profile_text(profile)])[0]
            points.append(
                {
                    "id": profile.id,
                    "vector": vec,
                    "payload": {
                        "display_name": profile.display_name,
                        "stage": profile.stage,
                        "goal": profile.goal,
                        "bottleneck": profile.bottleneck,
                        "bio": profile.bio,
                    },
                }
            )
        store.upsert_points("partner_profiles", points, vector_size=len(user_vector))
        qdrant_results = store.search(
            "partner_profiles", query_vector=user_vector, limit=max(limit, len(candidates))
        )
        for hit in qdrant_results:
            profile = candidate_map.get(str(hit["id"]))
            if profile is None or profile.id in seen:
                continue
            seen.add(profile.id)
            score = _score_boost(profile, user_profile, float(hit["score"]))
            ranked.append(_card_from_profile(profile, score, source_badge="Qdrant Cloud Match"))
            if len(ranked) >= limit:
                return ranked

    scored: list[tuple[PartnerProfile, float]] = []
    for profile in candidates:
        if profile.id in seen:
            continue
        vector = provider.embed([_profile_text(profile)])[0]
        similarity = _score_boost(
            profile, user_profile, _cosine_similarity(user_vector, vector)
        )
        scored.append((profile, similarity))

    scored.sort(key=lambda item: (-item[1], item[0].id))
    for profile, score in scored:
        ranked.append(
            _card_from_profile(profile, score, source_badge="Simulated prototype")
        )
        seen.add(profile.id)
        if len(ranked) >= limit:
            break
    return ranked[:limit]


def match_partner(
    user_profile: dict[str, str],
    candidates: list[PartnerProfile],
    *,
    embedder: EmbeddingProvider | None = None,
) -> PartnerMatchCard | None:
    """Return the best stage/goal match using Qdrant with cosine fallback."""
    ranked = rank_partners(user_profile, candidates, embedder=embedder, limit=1)
    return ranked[0] if ranked else None
