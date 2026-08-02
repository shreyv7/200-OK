"""Screen Time Evidence Processing Service.

Parses screen time screenshot data (or app duration payloads) using vision OCR
+ rule classifier, categorizes apps into creation/focus/drift categories,
builds a recommended schedule, and ingests evidence events into the database.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.schemas.evidence import EvidenceIngestRequest
from app.services.evidence import service as evidence_service

Category = Literal["creation", "passive_learning", "focus_drift"]


class AppUsageItem(BaseModel):
    appName: str = Field(alias="app_name")
    category: str  # creation, passive_learning, focus_drift
    durationMinutes: int = Field(alias="duration_minutes")
    confidence: float = 0.95

    model_config = {"populate_by_name": True}


class ScheduleBlock(BaseModel):
    startTime: str
    endTime: str
    label: str
    category: Category
    minutes: int
    rationale: str


class ScreenTimeAnalysisResult(BaseModel):
    totalMinutes: int
    focusMinutes: int
    learningMinutes: int
    driftMinutes: int
    apps: list[AppUsageItem]
    evidenceEventsCreated: int
    scoreDeltaEstimate: float
    schedule: list[ScheduleBlock] = Field(default_factory=list)
    ocrSource: str = "rules"


# Catalog mapping common apps to evidence categories & weights
APP_CATEGORY_RULES: dict[str, tuple[str, str, float]] = {
    # App name lower substring -> (category, evidence_type, base_weight)
    "github": ("creation", "github_commit", 4.0),
    "vscode": ("creation", "published_artifact", 4.5),
    "vs code": ("creation", "published_artifact", 4.5),
    "cursor": ("creation", "published_artifact", 4.5),
    "figma": ("creation", "published_artifact", 4.0),
    "notion": ("creation", "published_artifact", 3.0),
    "obsidian": ("creation", "published_artifact", 3.0),
    "terminal": ("creation", "published_artifact", 3.5),
    "xcode": ("creation", "published_artifact", 4.5),
    "sublime": ("creation", "published_artifact", 3.0),
    "android studio": ("creation", "published_artifact", 4.5),
    "photoshop": ("creation", "published_artifact", 3.5),
    "illustrator": ("creation", "published_artifact", 3.5),
    "productivity": ("creation", "published_artifact", 3.0),
    "kindle": ("passive_learning", "article_read", 2.0),
    "coursera": ("passive_learning", "article_read", 2.5),
    "udemy": ("passive_learning", "article_read", 2.5),
    "readwise": ("passive_learning", "article_read", 2.0),
    "duolingo": ("passive_learning", "article_read", 1.5),
    "stack overflow": ("passive_learning", "article_read", 2.0),
    "medium": ("passive_learning", "article_read", 1.5),
    "youtube": ("passive_learning", "article_read", 1.0),
    "safari": ("passive_learning", "article_read", 1.0),
    "chrome": ("passive_learning", "article_read", 1.0),
    "education": ("passive_learning", "article_read", 2.0),
    "reading": ("passive_learning", "article_read", 2.0),
    "instagram": ("focus_drift", "shortform_video_30min", -2.0),
    "tiktok": ("focus_drift", "shortform_video_30min", -2.5),
    "twitter": ("focus_drift", "shortform_video_30min", -1.5),
    " x ": ("focus_drift", "shortform_video_30min", -1.5),
    "reddit": ("focus_drift", "shortform_video_30min", -1.5),
    "facebook": ("focus_drift", "shortform_video_30min", -2.0),
    "reels": ("focus_drift", "shortform_video_30min", -2.5),
    "shorts": ("focus_drift", "shortform_video_30min", -2.5),
    "netflix": ("focus_drift", "shortform_video_30min", -2.0),
    "games": ("focus_drift", "shortform_video_30min", -2.0),
    "social": ("focus_drift", "shortform_video_30min", -2.0),
    "entertainment": ("focus_drift", "shortform_video_30min", -2.0),
    "whatsapp": ("focus_drift", "shortform_video_30min", -1.0),
    "messages": ("focus_drift", "shortform_video_30min", -1.0),
}


def parse_and_categorize_app(app_name: str, duration_minutes: int) -> tuple[str, str, float]:
    name_lower = f" {app_name.lower().strip()} "
    # Exact-ish match for lone "X"
    if app_name.lower().strip() in {"x", "twitter / x", "twitter/x"}:
        return "focus_drift", "shortform_video_30min", -1.5

    for keyword, (cat, ev_type, weight) in APP_CATEGORY_RULES.items():
        if keyword in name_lower or keyword.strip() in name_lower:
            return cat, ev_type, weight

    # Default fallback heuristics
    if any(w in name_lower for w in ["code", "dev", "studio", "notes", "write", "edit", "docs"]):
        return "creation", "published_artifact", 3.0
    if any(w in name_lower for w in ["learn", "book", "read", "news", "wiki", "paper"]):
        return "passive_learning", "article_read", 1.5

    # Neutral/Unclassified assumed slight drift if over 30 mins
    return "focus_drift", "shortform_video_30min", -1.0


def _fmt_time(minutes_from_midnight: int) -> str:
    minutes_from_midnight = max(0, min(minutes_from_midnight, 24 * 60 - 1))
    h, m = divmod(minutes_from_midnight, 60)
    return f"{h:02d}:{m:02d}"


def build_recommended_schedule(apps: list[AppUsageItem]) -> list[ScheduleBlock]:
    """Turn yesterday's usage into a protective schedule for the next day."""
    creation = sorted(
        [a for a in apps if a.category == "creation"],
        key=lambda a: a.durationMinutes,
        reverse=True,
    )
    learning = sorted(
        [a for a in apps if a.category == "passive_learning"],
        key=lambda a: a.durationMinutes,
        reverse=True,
    )
    drift = sorted(
        [a for a in apps if a.category == "focus_drift"],
        key=lambda a: a.durationMinutes,
        reverse=True,
    )

    creation_total = sum(a.durationMinutes for a in creation)
    learning_total = sum(a.durationMinutes for a in learning)
    drift_total = sum(a.durationMinutes for a in drift)

    # Protect / grow creation: at least 90m, or +30% over yesterday, capped 180m
    deep_work = min(180, max(90, int(creation_total * 1.3) if creation_total else 90))
    # Keep learning intentional but bounded
    learn_block = min(60, max(25, learning_total or 30))
    # Cap drift hard — cut yesterday's drift roughly in half, max 45m
    drift_budget = min(45, max(15, drift_total // 2 if drift_total else 20))

    top_creation = ", ".join(a.appName for a in creation[:2]) or "deep work tools"
    top_learning = ", ".join(a.appName for a in learning[:2]) or "reading / courses"
    top_drift = ", ".join(a.appName for a in drift[:2]) or "social apps"

    blocks: list[ScheduleBlock] = [
        ScheduleBlock(
            startTime="08:30",
            endTime=_fmt_time(8 * 60 + 30 + deep_work),
            label=f"Deep creation · {top_creation}",
            category="creation",
            minutes=deep_work,
            rationale=(
                f"Yesterday had {creation_total}m creation. Protect a {deep_work}m "
                "morning block before notifications."
            ),
        ),
        ScheduleBlock(
            startTime="13:30",
            endTime=_fmt_time(13 * 60 + 30 + learn_block),
            label=f"Focused learning · {top_learning}",
            category="passive_learning",
            minutes=learn_block,
            rationale=(
                f"Channel {learning_total}m of yesterday's learning into one "
                f"intentional {learn_block}m block."
            ),
        ),
        ScheduleBlock(
            startTime="19:30",
            endTime=_fmt_time(19 * 60 + 30 + drift_budget),
            label=f"Drift budget · {top_drift}",
            category="focus_drift",
            minutes=drift_budget,
            rationale=(
                f"Yesterday drifted {drift_total}m. Cap social/entertainment at "
                f"{drift_budget}m after work — then stop."
            ),
        ),
        ScheduleBlock(
            startTime="21:00",
            endTime="21:30",
            label="Shutdown review",
            category="creation",
            minutes=30,
            rationale="Log what shipped, pick tomorrow's single creation target.",
        ),
    ]
    return blocks


def process_screentime_payload(
    db: Session,
    user_id: str,
    parsed_apps: list[dict[str, Any]],
    *,
    ocr_source: str = "rules",
) -> ScreenTimeAnalysisResult:
    items: list[AppUsageItem] = []
    events_created = 0
    total_min = 0
    focus_min = 0
    learning_min = 0
    drift_min = 0
    score_delta = 0.0

    now = datetime.now(timezone.utc)

    for app in parsed_apps:
        name = str(app.get("appName") or app.get("app_name") or "Unknown App")
        duration = int(app.get("durationMinutes") or app.get("duration_minutes") or 0)
        if duration <= 0:
            continue

        category, ev_type, base_weight = parse_and_categorize_app(name, duration)

        items.append(
            AppUsageItem(
                app_name=name,
                category=category,
                duration_minutes=duration,
                confidence=0.96 if ocr_source == "vision" else 0.85,
            )
        )

        total_min += duration
        if category == "creation":
            focus_min += duration
            score_delta += base_weight * (duration / 30.0)
        elif category == "passive_learning":
            learning_min += duration
            score_delta += base_weight * (duration / 30.0)
        else:
            drift_min += duration
            score_delta += base_weight * (duration / 20.0)

        # Ingest Evidence Event into database
        event_req = EvidenceIngestRequest(
            userId=user_id,
            timestamp=now,
            source="trellis",
            type=ev_type,
            category=category,  # type: ignore
            value=float(duration),
            baseWeight=base_weight,
            metadata={
                "source": "screentime_drop_box",
                "appName": name,
                "durationMinutes": duration,
                "ocrSource": ocr_source,
            },
            simulated=False,
        )
        evidence_service.ingest(db, event_req)
        events_created += 1

    schedule = build_recommended_schedule(items)

    return ScreenTimeAnalysisResult(
        totalMinutes=total_min,
        focusMinutes=focus_min,
        learningMinutes=learning_min,
        driftMinutes=drift_min,
        apps=items,
        evidenceEventsCreated=events_created,
        scoreDeltaEstimate=round(score_delta, 2),
        schedule=schedule,
        ocrSource=ocr_source,
    )
