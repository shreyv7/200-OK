"""Weekly Becoming Report generator for AIA (PRD §6 F8).

Synthesizes evidence window and Gap score into an identity movement narrative
focusing on identity evolution, not hours or time tracking.
"""

from datetime import datetime, timezone
import uuid
from typing import Any, List, Optional

from app.schemas.evidence import EvidenceEvent
from app.schemas.identity import DeclaredSelf
from app.schemas.report import WeeklyReport
from app.services.identity.scoring.gap import GapResult


def _build_v0_fallback_report(
    user_id: str,
    gap_result: GapResult,
    prior_gap_score: Optional[int] = None,
    events: Optional[List[EvidenceEvent]] = None,
    ref_time: Optional[datetime] = None,
) -> WeeklyReport:
    """Deterministic v0 fallback report when LLM provider is not available."""
    if ref_time is None:
        ref_time = datetime.now(timezone.utc)

    gap_end = gap_result.gap_score
    gap_start = prior_gap_score if prior_gap_score is not None else gap_end
    gap_delta = gap_end - gap_start

    event_count = len(events) if events else 0
    creation_count = len([e for e in (events or []) if getattr(e, "category", "") == "creation" or getattr(e, "type", "") == "mission_completed"])

    if gap_delta < 0:
        narrative = (
            f"Identity Gap improved by {abs(gap_delta)} points. "
            f"Active engagement across {event_count} evidence touchpoints strengthened core identity attributes."
        )
    elif gap_delta > 0:
        narrative = (
            f"Identity Gap increased by {gap_delta} points. "
            f"Recent focus drift created a temporary deficit in active creation."
        )
    else:
        narrative = (
            f"Identity Gap remains steady at {gap_end} points. "
            f"Consistent baseline activity across {event_count} evidence events maintained momentum."
        )

    highlights = [
        f"Completed {creation_count} creation touchpoints across the evidence window.",
        f"Overall identity alignment currently stands at {gap_result.alignment}%.",
    ]

    return WeeklyReport(
        id=f"rep_{uuid.uuid4().hex[:12]}",
        userId=user_id,
        gapScoreStart=gap_start,
        gapScoreEnd=gap_end,
        gapDelta=gap_delta,
        narrative=narrative,
        highlights=highlights,
        generatedAt=ref_time,
        simulated=True,
    )


def generate_weekly_report(
    user_id: str,
    declared_self: DeclaredSelf,
    events: List[EvidenceEvent],
    gap_result: GapResult,
    prior_gap_score: Optional[int] = None,
    llm_provider: Optional[Any] = None,
    ref_time: Optional[datetime] = None,
) -> WeeklyReport:
    """Generates a WeeklyReport given user_id, DeclaredSelf, events, and GapResult."""
    if ref_time is None:
        ref_time = datetime.now(timezone.utc)

    if not llm_provider:
        return _build_v0_fallback_report(user_id, gap_result, prior_gap_score, events, ref_time)

    try:
        gap_end = gap_result.gap_score
        gap_start = prior_gap_score if prior_gap_score is not None else gap_end
        gap_delta = gap_end - gap_start

        # Prepare evidence summary for LLM
        summary_lines = [f"- {e.type} ({e.category if hasattr(e, 'category') else 'evidence'})" for e in events[:10]]
        evidence_str = "\n".join(summary_lines) if summary_lines else "No recent events"

        messages = [
            {
                "role": "system",
                "content": (
                    "You are the Trellis Weekly Becoming Report generator. "
                    "Focus on identity movement, NOT hours or time-tracking. "
                    "Return JSON with 'narrative' (string) and 'highlights' (array of strings)."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"User: {user_id}\n"
                    f"Gap score start: {gap_start}, end: {gap_end}, delta: {gap_delta}\n"
                    f"Evidence touchpoints:\n{evidence_str}"
                ),
            },
        ]

        schema = {
            "type": "object",
            "properties": {
                "narrative": {"type": "string"},
                "highlights": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["narrative", "highlights"],
        }

        if hasattr(llm_provider, "generate_structured"):
            res = llm_provider.generate_structured(schema=schema, messages=messages)
        elif hasattr(llm_provider, "generate"):
            res = llm_provider.generate(messages)
        else:
            return _build_v0_fallback_report(user_id, gap_result, prior_gap_score, events, ref_time)

        if isinstance(res, dict) and "narrative" in res and "highlights" in res:
            return WeeklyReport(
                id=f"rep_{uuid.uuid4().hex[:12]}",
                userId=user_id,
                gapScoreStart=gap_start,
                gapScoreEnd=gap_end,
                gapDelta=gap_delta,
                narrative=str(res["narrative"]),
                highlights=[str(h) for h in res.get("highlights", []) if isinstance(h, (str, int))],
                generatedAt=ref_time,
                simulated=True,
            )

        return _build_v0_fallback_report(user_id, gap_result, prior_gap_score, events, ref_time)

    except Exception:
        return _build_v0_fallback_report(user_id, gap_result, prior_gap_score, events, ref_time)
