"""Deterministic Gap formula constants and thresholds.

PRD §9 Source of Truth — LLMs NEVER modify or compute these numbers.
"""

import math

# Exponential recency decay half-life parameter (7 days half-life)
HALF_LIFE_DAYS: float = 7.0
LAMBDA: float = math.log(2.0) / HALF_LIFE_DAYS

# Fixed evidence weights per PRD §9
EVENT_WEIGHTS: dict[str, float] = {
    "mission_completed": 3.0,
    "github_commit": 4.0,
    "published_artifact": 5.0,
    "attended_experience": 4.0,
    "passive_item": 1.0,
    "focus_drift_10min": -2.0,
    # Notion connector (PRD §9 — creation signals)
    "notion_page_created": 3.0,  # Creating a new page = high-value creation
    "notion_page_edited": 1.5,   # Editing an existing page = lighter creation signal
    # Companion (Tampermonkey) aliases — userscript normally normalizes to
    # passive_item / focus_drift_10min; these keep older payloads scorable.
    "session_started": 1.0,
    "feed_entered": 1.0,
    "feed_exited": 1.0,
    "feed_scroll": 1.0,
    "spa_navigation": 1.0,
    "tab_hidden": 1.0,
    "tab_visible": 1.0,
    "reel_view": 1.0,
    "watch_view": 1.0,
    "focus_drift_excessive_continuous_scrolling": -2.0,
    "focus_drift_long_continuous_scrolling": -2.0,
    "focus_drift_excessive_reel_consumption": -2.0,
    "focus_drift_excessive_reel_dwell": -2.0,
}

# Category classification sets
CREATION_TYPES: set[str] = {
    "mission_completed",
    "github_commit",
    "published_artifact",
    "attended_experience",
    "notion_page_created",
    "notion_page_edited",
}

PASSIVE_TYPES: set[str] = {
    "passive_item",
    "session_started",
    "feed_entered",
    "feed_exited",
    "feed_scroll",
    "spa_navigation",
    "tab_hidden",
    "tab_visible",
    "reel_view",
    "watch_view",
}

DRIFT_TYPES: set[str] = {
    "focus_drift_10min",
    "focus_drift_excessive_continuous_scrolling",
    "focus_drift_long_continuous_scrolling",
    "focus_drift_excessive_reel_consumption",
    "focus_drift_excessive_reel_dwell",
}

# Capacity Tier thresholds (0-100 scale)
CAPACITY_FULL_MIN: int = 67
CAPACITY_LIGHT_MIN: int = 34
CAPACITY_MICRO_MIN: int = 0

# Trust Ledger System Unlearning failure thresholds
DISMISSAL_FAILURE_THRESHOLD: int = 3
DISMISSAL_WINDOW_DAYS: int = 14

# Default target evidence points per attribute when unstated
DEFAULT_DECLARED_TARGET: float = 15.0

# Gap score delta threshold to trigger stack invalidation
GAP_DELTA_INVALIDATION_THRESHOLD: float = 5.0

# Guardian / Intervention budget constants per PRD §6 F6
INTERVENTION_DAILY_CAP: int = 5
INTERVENTION_MIN_SPACING_HOURS: float = 1.0
HIGH_DISMISSAL_RATE_THRESHOLD: float = 0.6

