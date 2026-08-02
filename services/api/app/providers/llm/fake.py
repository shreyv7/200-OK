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
            return dict(_DEFAULT_DECLARED_SELF_ATTRIBUTES)

        if "apps" in properties:
            return {
                "apps": [
                    {"appName": "VS Code", "durationMinutes": 105},
                    {"appName": "Figma", "durationMinutes": 40},
                    {"appName": "YouTube", "durationMinutes": 35},
                    {"appName": "Instagram", "durationMinutes": 95},
                    {"appName": "Twitter", "durationMinutes": 45},
                ],
                "sourceLabel": "iOS Screen Time",
            }

        return {"status": "ok"}

    def generate_structured_from_image(
        self,
        schema: dict[str, Any],
        prompt: str,
        image_bytes: bytes,
        mime_type: str = "image/png",
        opts: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        self.calls.append(
            {
                "schema": schema,
                "prompt": prompt,
                "mime_type": mime_type,
                "image_bytes": len(image_bytes),
                "opts": opts or {},
                "mode": "image",
            }
        )
        if self.response is not None:
            return dict(self.response)
        return self.generate_structured(schema, [{"role": "user", "content": prompt}], opts)
