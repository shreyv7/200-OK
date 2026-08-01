from __future__ import annotations

from app.providers.embeddings import FakeEmbeddingProvider
from app.services.recommendation.partner_match import match_partner
from tests.fixtures.sample_data import sample_partner_profiles, sample_partner_user_profile


def test_partner_match_is_deterministic_and_prototype_labeled() -> None:
    user_profile = sample_partner_user_profile()
    candidates = sample_partner_profiles()
    embedder = FakeEmbeddingProvider()

    first = match_partner(user_profile, candidates, embedder=embedder)
    second = match_partner(user_profile, candidates, embedder=embedder)

    assert first is not None
    assert first == second
    assert first.source_badge == "Simulated prototype"
    assert first.profile_id in {profile.id for profile in candidates}


def test_partner_match_prefers_stage_and_bottleneck_overlap() -> None:
    user_profile = {
        "stage": "early",
        "goal": "public speaking",
        "bottleneck": "confidence",
        "summary": "Wants to speak in public.",
    }
    card = match_partner(user_profile, sample_partner_profiles())
    assert card is not None
    assert card.profile_id == "partner-1"
