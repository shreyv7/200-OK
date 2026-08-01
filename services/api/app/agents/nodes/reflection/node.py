"""Trust Ledger reflection — evidence intake during curation."""

from __future__ import annotations

from typing import Any

from app.services.recommendation.reflection_ledger import attach_evidence


def reflection_node(state: dict[str, Any]) -> dict[str, Any]:
    evidence_id = state.get("evidence_id")
    stack_data = state.get("identity_stack") or {}
    stack_draft = state.get("stack_draft") or {}
    hypothesis_id = (
        state.get("hypothesis_id")
        or stack_data.get("hypothesisId")
        or stack_draft.get("hypothesis_id")
    )

    if evidence_id and hypothesis_id:
        attach_evidence(str(hypothesis_id), [str(evidence_id)])

    return {"visited": ["reflection"]}
