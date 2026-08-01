"""Weekly Report + Identity Evolution wiring. Owner: Backend. milestones.md M7 (F8/F11).

Same pattern as M3's onboarding_orchestration.py: Backend builds the
calling contract (load data, format AIA's prompt, call the real
LLMProvider, validate a narrow extraction schema) — AIA owns refining
the prompt content itself.
"""

from __future__ import annotations

import json

from pydantic import BaseModel, ValidationError

from app.prompts.loader import load_prompt
from app.providers.llm.base import LLMProvider
from app.repositories import evidence_repository, evolution_repository, twin_repository
from app.schemas.agent_run import IdentityEvolutionProposal, WeeklyReport
from app.schemas.identity import IdentityAttribute

WINDOW_EVENT_LIMIT = 200


class _EvolutionExtraction(BaseModel):
    """What the LLM actually returns for an evolution proposal — Backend
    assigns id/userId/status/createdAt, not the model."""

    proposedAttributes: list[IdentityAttribute]
    citedEvidenceIds: list[str]
    rationale: str


def _evidence_summary(db, user_id: str) -> list[dict]:
    rows = evidence_repository.list_window(db, user_id, limit=WINDOW_EVENT_LIMIT)
    return [
        {"id": r.id, "type": r.type, "category": r.category, "timestamp": r.timestamp.isoformat()}
        for r in rows
    ]


def generate_weekly_report(db, llm_provider: LLMProvider, user_id: str) -> WeeklyReport:
    declared_self = twin_repository.get_active_declared_self(db, user_id)
    events = _evidence_summary(db, user_id)

    template = load_prompt("identity/weekly_report_v1")
    schema = WeeklyReport.model_json_schema()
    prompt = template.replace(
        "{declared_self_json}",
        json.dumps(declared_self.model_dump(mode="json") if declared_self else {}),
    ).replace("{evidence_summary_json}", json.dumps(events)).replace(
        "{output_schema_json}", json.dumps(schema)
    )
    messages = [
        {"role": "system", "content": "You are the Trellis Weekly Report Agent."},
        {"role": "user", "content": prompt},
    ]

    raw = llm_provider.generate_structured(schema=schema, messages=messages)
    return WeeklyReport.model_validate(raw)


def generate_evolution_proposal(
    db, llm_provider: LLMProvider, user_id: str
) -> IdentityEvolutionProposal:
    declared_self = twin_repository.get_active_declared_self(db, user_id)
    events = _evidence_summary(db, user_id)

    template = load_prompt("identity/evolution_proposal_v1")
    schema = _EvolutionExtraction.model_json_schema()
    prompt = (
        f"{template}\n\nDeclared Self: {json.dumps(declared_self.model_dump(mode='json') if declared_self else {})}"
        f"\nEvidence window: {json.dumps(events)}\nRequired JSON Schema: {json.dumps(schema)}"
    )
    messages = [
        {"role": "system", "content": "You are the Trellis Identity Evolution Agent."},
        {"role": "user", "content": prompt},
    ]

    raw = llm_provider.generate_structured(schema=schema, messages=messages)
    try:
        extraction = _EvolutionExtraction.model_validate(raw)
    except ValidationError as first_error:
        messages.append(
            {
                "role": "user",
                "content": f"Your previous output was invalid: {first_error}. Return valid JSON matching the schema exactly.",
            }
        )
        raw_retry = llm_provider.generate_structured(schema=schema, messages=messages)
        extraction = _EvolutionExtraction.model_validate(raw_retry)

    return evolution_repository.create(
        db,
        user_id=user_id,
        proposed_attributes=extraction.proposedAttributes,
        cited_evidence_ids=extraction.citedEvidenceIds,
        rationale=extraction.rationale,
    )
