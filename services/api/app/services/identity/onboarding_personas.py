"""Curated onboarding paths. They are starting hypotheses, never identities.

The user still confirms the extracted Declared Self before it can be measured.
"""

from __future__ import annotations

from app.schemas.onboarding import OnboardingPersona, OnboardingQuestion


def _questions(rows: list[tuple[str, str, str, list[str]]]) -> list[OnboardingQuestion]:
    return [OnboardingQuestion(id=i, prompt=p, hint=h, options=o) for i, p, h, o in rows]


PERSONAS: tuple[OnboardingPersona, ...] = (
    OnboardingPersona(
        id="career_pivot",
        title="Career Pivot",
        description="Move from an unclear next step to credible, visible career momentum.",
        outcome="A transition plan with proof-of-skill and outreach markers.",
        questions=_questions([
            ("aspiration", "What direction are you moving toward?", "Target role or field.", ["A product role", "A software role", "A creative or research role"]),
            ("why", "Why is this transition important now?", "The cost of waiting.", ["I want work that fits my strengths", "I need a clearer path", "I have an opportunity approaching"]),
            ("habits", "What are you doing for the transition today?", "Current evidence.", ["Learning but not showing my work", "Applying inconsistently", "Avoiding conversations and outreach"]),
            ("blocker", "What is the biggest constraint?", "Bottleneck seed.", ["I do not feel credible yet", "I lack a portfolio", "I do not know who to talk to"]),
            ("capacity", "How much weekly capacity is realistic?", "Guardian sizing.", ["2–3 hours", "4–6 hours", "7+ hours"]),
        ]),
    ),
    OnboardingPersona(
        id="research_to_output",
        title="Research to Output",
        description="Turn deep learning into visible writing, projects, or teaching.",
        outcome="A knowledge-to-output identity with shipping markers.",
        questions=_questions([
            ("aspiration", "What do you want to be known for understanding?", "Knowledge direction.", ["A technical subject", "A business or policy topic", "A creative craft"]),
            ("why", "Why should this become visible now?", "Reason for output.", ["To build credibility", "To help others learn", "To create career options"]),
            ("habits", "How do you learn today?", "Revealed baseline.", ["I save more than I publish", "I take notes but do not synthesize", "I start many courses"]),
            ("blocker", "What stops you from sharing?", "Bottleneck seed.", ["Perfectionism", "No repeatable process", "I doubt my perspective"]),
            ("capacity", "What can you sustain each week?", "Guardian sizing.", ["One short session", "Two focused sessions", "Three or more sessions"]),
        ]),
    ),
    OnboardingPersona(
        id="community_leader",
        title="Community Leader",
        description="Grow the confidence and consistency to convene, contribute, and lead.",
        outcome="A leadership identity grounded in contribution and real-world reps.",
        questions=_questions([
            ("aspiration", "What kind of community impact do you want to have?", "Leadership direction.", ["Host useful conversations", "Mentor and support peers", "Lead a project or initiative"]),
            ("why", "Why does that matter to you?", "Personal value.", ["I want to create belonging", "I want to grow my leadership", "I see a problem worth solving"]),
            ("habits", "How do you participate today?", "Revealed baseline.", ["I mostly observe", "I contribute occasionally", "I help but avoid leading"]),
            ("blocker", "What keeps you from stepping forward?", "Bottleneck seed.", ["Fear of being judged", "Difficulty following through", "I lack a network"]),
            ("capacity", "What commitment can you protect weekly?", "Guardian sizing.", ["15 minutes", "One hour", "Two or more hours"]),
        ]),
    ),
    OnboardingPersona(
        id="creative_practice",
        title="Creative Practice",
        description="Build a sustainable practice and a portfolio of finished work.",
        outcome="A creative identity with practice, completion, and sharing markers.",
        questions=_questions([
            ("aspiration", "What creative practice do you want to grow?", "Creative direction.", ["Writing", "Design or visual work", "Music, video, or performance"]),
            ("why", "Why do you want this practice now?", "Meaning and urgency.", ["I want a portfolio", "I want to express an idea", "I want a disciplined creative life"]),
            ("habits", "What happens in a typical week?", "Revealed baseline.", ["I collect inspiration but do not make", "I begin work but leave it unfinished", "I practice only when motivated"]),
            ("blocker", "What is hardest right now?", "Bottleneck seed.", ["Starting", "Finishing", "Sharing work publicly"]),
            ("capacity", "How much protected practice is realistic?", "Guardian sizing.", ["15 minutes a day", "Three sessions a week", "A longer weekly block"]),
        ]),
    ),
)


def list_personas() -> list[OnboardingPersona]:
    return list(PERSONAS)


def get_persona(persona_id: str | None) -> OnboardingPersona | None:
    return next((persona for persona in PERSONAS if persona.id == persona_id), None)


def get_persona_from_context(context: str | None) -> OnboardingPersona | None:
    return next((persona for persona in PERSONAS if context and persona.title in context), None)
