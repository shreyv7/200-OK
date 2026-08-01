"""Screen Time Evidence Processing Service.

Parses screen time screenshot data (or app duration payloads) using rules + AI provider,
categorizes apps into creation/focus/drift categories, and ingests evidence events into the database.
"""

from __future__ import annotations

import base64
from datetime import datetime, timezone
from typing import Any
from pydantic import BaseModel, Field

from sqlalchemy.orm import Session
from app.schemas.evidence import EvidenceIngestRequest
from app.services.evidence import service as evidence_service


class AppUsageItem(BaseModel):
    appName: str = Field(alias="app_name")
    category: str  # creation, passive_learning, focus_drift
    durationMinutes: int = Field(alias="duration_minutes")
    confidence: float = 0.95


class ScreenTimeAnalysisResult(BaseModel):
    totalMinutes: int
    focusMinutes: int
    learningMinutes: int
    driftMinutes: int
    apps: list[AppUsageItem]
    evidenceEventsCreated: int
    scoreDeltaEstimate: float


# Catalog mapping common apps to evidence categories & weights
APP_CATEGORY_RULES: dict[str, tuple[str, str, float]] = {
    # App name lower substring -> (category, evidence_type, base_weight)
    "github": ("creation", "github_commit", 4.0),
    "vscode": ("creation", "published_artifact", 4.5),
    "cursor": ("creation", "published_artifact", 4.5),
    "figma": ("creation", "published_artifact", 4.0),
    "notion": ("creation", "published_artifact", 3.0),
    "obsidian": ("creation", "published_artifact", 3.0),
    "terminal": ("creation", "published_artifact", 3.5),
    "xcode": ("creation", "published_artifact", 4.5),
    "sublime": ("creation", "published_artifact", 3.0),
    "kindle": ("passive_learning", "article_read", 2.0),
    "coursera": ("passive_learning", "article_read", 2.5),
    "udemy": ("passive_learning", "article_read", 2.5),
    "readwise": ("passive_learning", "article_read", 2.0),
    "duolingo": ("passive_learning", "article_read", 1.5),
    "stack overflow": ("passive_learning", "article_read", 2.0),
    "medium": ("passive_learning", "article_read", 1.5),
    "youtube": ("passive_learning", "article_read", 1.0),
    "instagram": ("focus_drift", "shortform_video_30min", -2.0),
    "tiktok": ("focus_drift", "shortform_video_30min", -2.5),
    "twitter": ("focus_drift", "shortform_video_30min", -1.5),
    "x": ("focus_drift", "shortform_video_30min", -1.5),
    "reddit": ("focus_drift", "shortform_video_30min", -1.5),
    "facebook": ("focus_drift", "shortform_video_30min", -2.0),
    "reels": ("focus_drift", "shortform_video_30min", -2.5),
    "netflix": ("focus_drift", "shortform_video_30min", -2.0),
    "games": ("focus_drift", "shortform_video_30min", -2.0),
}


def parse_and_categorize_app(app_name: str, duration_minutes: int) -> tuple[str, str, float]:
    name_lower = app_name.lower().strip()
    for keyword, (cat, ev_type, weight) in APP_CATEGORY_RULES.items():
        if keyword in name_lower:
            return cat, ev_type, weight
    
    # Default fallback heuristics
    if any(w in name_lower for w in ["code", "dev", "studio", "notes", "write", "edit", "docs"]):
        return "creation", "published_artifact", 3.0
    if any(w in name_lower for w in ["learn", "book", "read", "news", "wiki", "paper"]):
        return "passive_learning", "article_read", 1.5
    
    # Neutral/Unclassified assumed slight drift if over 30 mins
    return "focus_drift", "shortform_video_30min", -1.0


def process_screentime_payload(
    db: Session,
    user_id: str,
    parsed_apps: list[dict[str, Any]],
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
                confidence=0.96,
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
            },
            simulated=False,
        )
        evidence_service.ingest(db, event_req)
        events_created += 1

    return ScreenTimeAnalysisResult(
        totalMinutes=total_min,
        focusMinutes=focus_min,
        learningMinutes=learning_min,
        driftMinutes=drift_min,
        apps=items,
        evidenceEventsCreated=events_created,
        scoreDeltaEstimate=round(score_delta, 2),
    )
