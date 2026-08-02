"""Screen Time OCR + classifier + schedule tests."""

from __future__ import annotations

from app.providers.llm.fake import FakeLLMProvider
from app.services.screentime.service import (
    AppUsageItem,
    build_recommended_schedule,
    parse_and_categorize_app,
    process_screentime_payload,
)
from app.services.screentime.vision import extract_apps_from_screenshot
from tests.conftest import ensure_user


def test_extract_apps_from_screenshot_uses_vision_llm() -> None:
    llm = FakeLLMProvider()
    apps = extract_apps_from_screenshot(llm, b"fake-image-bytes", mime_type="image/png")
    assert len(apps) >= 3
    assert all(a["durationMinutes"] > 0 for a in apps)
    assert llm.calls and llm.calls[0]["mode"] == "image"


def test_classifier_maps_creation_and_drift() -> None:
    assert parse_and_categorize_app("VS Code", 60)[0] == "creation"
    assert parse_and_categorize_app("Instagram Reels", 40)[0] == "focus_drift"
    assert parse_and_categorize_app("Kindle", 25)[0] == "passive_learning"


def test_schedule_protects_creation_and_caps_drift() -> None:
    apps = [
        AppUsageItem(app_name="Cursor", category="creation", duration_minutes=60),
        AppUsageItem(app_name="YouTube", category="passive_learning", duration_minutes=40),
        AppUsageItem(app_name="TikTok", category="focus_drift", duration_minutes=120),
    ]
    schedule = build_recommended_schedule(apps)
    assert len(schedule) >= 3
    creation = next(b for b in schedule if "Deep creation" in b.label)
    drift = next(b for b in schedule if "Drift budget" in b.label)
    assert creation.minutes >= 90
    assert drift.minutes <= 60


def test_process_payload_returns_schedule(db_session) -> None:
    user_id = "screentime-user"
    ensure_user(db_session, user_id)
    result = process_screentime_payload(
        db_session,
        user_id,
        [
            {"appName": "Figma", "durationMinutes": 50},
            {"appName": "Instagram", "durationMinutes": 80},
        ],
        ocr_source="vision",
    )
    assert result.totalMinutes == 130
    assert result.focusMinutes == 50
    assert result.driftMinutes == 80
    assert result.ocrSource == "vision"
    assert len(result.schedule) >= 3
    assert result.evidenceEventsCreated == 2
