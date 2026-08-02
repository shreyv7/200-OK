"""Screen Time screenshot OCR via multimodal LLM. Owner: Backend.

Uses LLMProvider.generate_structured_from_image (Gemini vision in prod,
FakeLLMProvider in tests). Does not import google.genai directly
(techstack §11.1).
"""

from __future__ import annotations

from typing import Any

from app.providers.llm.base import LLMProvider

SCREEN_TIME_OCR_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "sourceLabel": {
            "type": "string",
            "description": "e.g. iOS Screen Time, Android Digital Wellbeing, Unknown",
        },
        "apps": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "appName": {"type": "string"},
                    "durationMinutes": {"type": "integer", "minimum": 1},
                },
                "required": ["appName", "durationMinutes"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["apps"],
    "additionalProperties": False,
}

_OCR_PROMPT = """You are an OCR + vision extractor for phone Screen Time reports.

Read the attached screenshot (iOS Screen Time or Android Digital Wellbeing).
Extract every app / category row that shows a usage duration.

Rules:
- Convert durations like "1h 45m", "45 min", "2 hr" into integer minutes.
- Use the visible app or category name as appName (keep it short and readable).
- Skip totals-only rows if individual apps are listed; prefer per-app rows.
- If a row is a category bucket (e.g. Social, Productivity), still include it.
- Ignore UI chrome (Settings, Edit, See All) that is not a usage row.
- Return at least one app if any duration is visible.
- Do not invent apps that are not in the image.
"""


def extract_apps_from_screenshot(
    llm: LLMProvider,
    image_bytes: bytes,
    mime_type: str = "image/png",
) -> list[dict[str, Any]]:
    """OCR a screentime screenshot into [{appName, durationMinutes}, ...]."""
    if not image_bytes:
        raise ValueError("Empty screenshot upload")

    raw = llm.generate_structured_from_image(
        SCREEN_TIME_OCR_SCHEMA,
        _OCR_PROMPT,
        image_bytes,
        mime_type=mime_type,
    )
    apps = raw.get("apps") or []
    cleaned: list[dict[str, Any]] = []
    for app in apps:
        name = str(app.get("appName") or app.get("app_name") or "").strip()
        try:
            minutes = int(app.get("durationMinutes") or app.get("duration_minutes") or 0)
        except (TypeError, ValueError):
            minutes = 0
        if name and minutes > 0:
            cleaned.append({"appName": name, "durationMinutes": minutes})

    if not cleaned:
        raise ValueError("No app durations could be read from this screenshot")
    return cleaned


def guess_mime_type(filename: str, content_type: str | None) -> str:
    if content_type and content_type.startswith("image/"):
        return content_type
    lower = filename.lower()
    if lower.endswith(".jpg") or lower.endswith(".jpeg"):
        return "image/jpeg"
    if lower.endswith(".webp"):
        return "image/webp"
    if lower.endswith(".gif"):
        return "image/gif"
    return "image/png"
