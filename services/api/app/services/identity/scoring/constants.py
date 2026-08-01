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
}

# Category classification sets
CREATION_TYPES: set[str] = {
    "mission_completed",
    "github_commit",
    "published_artifact",
    "attended_experience",
}

PASSIVE_TYPES: set[str] = {
    "passive_item",
}

DRIFT_TYPES: set[str] = {
    "focus_drift_10min",
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
