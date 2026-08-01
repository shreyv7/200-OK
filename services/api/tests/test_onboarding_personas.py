from __future__ import annotations

from app.providers.llm.fake import FakeLLMProvider
from app.schemas.onboarding import OnboardingPersona
from app.services.identity.onboarding_personas import get_persona, list_personas


def test_persona_catalog_is_distinct_and_interview_sized() -> None:
    personas = list_personas()
    assert len({persona.id for persona in personas}) == len(personas)
    assert {persona.id for persona in personas} == {
        "career_pivot",
        "research_to_output",
        "community_leader",
        "creative_practice",
    }
    assert all(isinstance(persona, OnboardingPersona) and len(persona.questions) == 5 for persona in personas)


def test_fake_provider_returns_persona_appropriate_declared_self() -> None:
    provider = FakeLLMProvider()
    response = provider.generate_structured(
        schema={"properties": {"attributes": {}}},
        messages=[{"role": "user", "content": "Selected onboarding path: Career Pivot."}],
    )
    assert response["attributes"][0]["id"] == "career_navigator"
    assert get_persona("career_pivot") is not None
    assert get_persona("not-a-persona") is None
