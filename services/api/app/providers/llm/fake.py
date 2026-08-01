from __future__ import annotations

from typing import Any

from app.providers.llm.base import LLMProvider

# Used when local/CI runs Mirror Interview extraction without a live Gemini key.
_DEFAULT_DECLARED_SELF_ATTRIBUTES: dict[str, Any] = {
    "attributes": [
        {
            "id": "public_speaker",
            "label": "Confident Public Speaker",
            "weight": 0.5,
            "targetWeeklyPoints": 15.0,
            "markers": [
                {"id": "speaks_publicly", "label": "Speaks in front of others"},
                {"id": "practices_delivery", "label": "Practices a talk out loud"},
            ],
        },
        {
            "id": "builder",
            "label": "Builder Who Ships Projects",
            "weight": 0.5,
            "targetWeeklyPoints": 15.0,
            "markers": [
                {"id": "ships_code", "label": "Commits and publishes code"},
                {"id": "closes_milestones", "label": "Closes a project milestone"},
            ],
        },
    ]
}

_PERSONA_ATTRIBUTES: dict[str, dict[str, Any]] = {
    "Career Pivot": {"attributes": [{"id": "career_navigator", "label": "Career Navigator", "weight": 0.55, "targetWeeklyPoints": 12.0, "markers": [{"id": "builds_portfolio", "label": "Builds visible proof of skill"}, {"id": "does_outreach", "label": "Starts relevant career conversations"}]}, {"id": "consistent_applicant", "label": "Consistent Opportunity Seeker", "weight": 0.45, "targetWeeklyPoints": 10.0, "markers": [{"id": "targets_roles", "label": "Targets a specific next role"}, {"id": "follows_up", "label": "Follows up on applications and conversations"}]}]},
    "Research to Output": {"attributes": [{"id": "public_synthesizer", "label": "Public Knowledge Synthesizer", "weight": 0.55, "targetWeeklyPoints": 12.0, "markers": [{"id": "writes_summaries", "label": "Publishes concise learning summaries"}, {"id": "connects_ideas", "label": "Connects research to practical problems"}]}, {"id": "consistent_learner", "label": "Deliberate Learner", "weight": 0.45, "targetWeeklyPoints": 10.0, "markers": [{"id": "finishes_learning", "label": "Finishes focused learning sessions"}, {"id": "turns_learning_into_output", "label": "Turns learning into an artifact"}]}]},
    "Community Leader": {"attributes": [{"id": "community_contributor", "label": "Community Contributor", "weight": 0.5, "targetWeeklyPoints": 10.0, "markers": [{"id": "makes_introductions", "label": "Makes useful introductions"}, {"id": "contributes_publicly", "label": "Contributes in community spaces"}]}, {"id": "initiative_leader", "label": "Initiative Leader", "weight": 0.5, "targetWeeklyPoints": 12.0, "markers": [{"id": "hosts_sessions", "label": "Hosts or facilitates a useful session"}, {"id": "follows_through", "label": "Follows through on commitments"}]}]},
    "Creative Practice": {"attributes": [{"id": "creative_practitioner", "label": "Consistent Creative Practitioner", "weight": 0.5, "targetWeeklyPoints": 12.0, "markers": [{"id": "practices_craft", "label": "Practices the craft on a schedule"}, {"id": "finishes_pieces", "label": "Finishes small creative pieces"}]}, {"id": "portfolio_sharer", "label": "Portfolio Sharer", "weight": 0.5, "targetWeeklyPoints": 10.0, "markers": [{"id": "shares_work", "label": "Shares finished work"}, {"id": "reflects_on_feedback", "label": "Reflects on feedback and improves"}]}]},
}


class FakeLLMProvider(LLMProvider):
    """Deterministic LLM stub for tests and local wiring."""

    def __init__(self, response: dict[str, Any] | None = None) -> None:
        self.response = response
        self.calls: list[dict[str, Any]] = []

    def generate_structured(
        self,
        schema: dict[str, Any],
        messages: list[dict[str, str]],
        opts: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        self.calls.append(
            {"schema": schema, "messages": messages, "opts": opts or {}}
        )
        if self.response is not None:
            return dict(self.response)

        properties = schema.get("properties") or {}
        if "attributes" in properties:
            transcript = "\n".join(message.get("content", "") for message in messages)
            for persona_title, attributes in _PERSONA_ATTRIBUTES.items():
                if persona_title in transcript:
                    return dict(attributes)
            return dict(_DEFAULT_DECLARED_SELF_ATTRIBUTES)

        return {"status": "ok"}
