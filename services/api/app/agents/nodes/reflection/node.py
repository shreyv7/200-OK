from __future__ import annotations

from typing import Any

from app.services.recommendation.ledger_intake import record_evidence_ids


def reflection_node(state: dict[str, Any]) -> dict[str, Any]:
    evidence_id = state.get("evidence_id")
    stack_draft = state.get("stack_draft") or {}
    hypothesis_id = stack_draft.get("hypothesis_id") or state.get("hypothesis_id")

    if evidence_id and hypothesis_id:
        record_evidence_ids(str(hypothesis_id), [str(evidence_id)])

    return {"visited": ["reflection"]}
