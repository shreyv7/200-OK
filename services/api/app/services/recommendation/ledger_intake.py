"""In-memory evidence-ID intake for Reflection/Ledger outcome windows (M1).

Persistence and verdict logic land in M5.
"""

from __future__ import annotations

from datetime import datetime, timezone

_intake_store: dict[str, list[tuple[str, datetime]]] = {}


def record_evidence_ids(hypothesis_id: str, evidence_ids: list[str]) -> None:
    """Associate evidence IDs with a hypothesis for a future outcome window."""
    if not evidence_ids:
        return
    now = datetime.now(timezone.utc)
    entries = _intake_store.setdefault(hypothesis_id, [])
    for evidence_id in evidence_ids:
        if evidence_id:
            entries.append((evidence_id, now))


def get_pending_window(hypothesis_id: str) -> list[str]:
    """Return evidence IDs recorded for the hypothesis (deduped, insertion order)."""
    seen: set[str] = set()
    ordered: list[str] = []
    for evidence_id, _ in _intake_store.get(hypothesis_id, []):
        if evidence_id not in seen:
            seen.add(evidence_id)
            ordered.append(evidence_id)
    return ordered


def clear_intake_store() -> None:
    """Test helper — reset in-memory intake."""
    _intake_store.clear()
