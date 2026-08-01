"""Registers the evidence.created -> Gap recompute hook. Owner: Backend.

Closes the M1->M2 loop from milestones.md: "Recompute on every accepted
evidence event (called from Backend service)".

Note: AIS's `app.services.recommendation.evidence_hook.emit_evidence_created`
is a second, still-dangling subscriber seam (its own docstring says
"Backend M1 wires `emit_evidence_created` after persistence" — nobody
calls it yet, on this branch or on merged `dev`). Deliberately not wired
here: it invokes AIS's LangGraph coordinator, which is their code path to
own and test, not something Backend should trigger blind. Flagged in the
M2 Done report for a human to route to AIS.
"""

from __future__ import annotations

from app.core.db import SessionLocal
from app.models.evidence_event import EvidenceEventModel
from app.services.evidence import service as evidence_service
from app.services.identity import orchestration


def _on_evidence_created(row: EvidenceEventModel) -> None:
    db = SessionLocal()
    try:
        orchestration.recompute_and_persist(db, row.user_id)
    finally:
        db.close()


def register() -> None:
    evidence_service.on_evidence_created(_on_evidence_created)
