"""LLM-Driven Bottleneck Packet v1 Generator for AIA.

Uses LLMProvider facade with bottleneck_diagnosis_v1 prompt to diagnose Potential Bottleneck candidates.
Maintains Gap Firewall: never modifies or recomputes deterministic GapResult.
"""

import json
from typing import Any, List, Optional

from app.prompts.loader import load_prompt
from app.providers.llm.repair import generate_structured_with_repair
from app.schemas.evidence import EvidenceEvent
from app.services.decision.packet import BOTTLENECK_TAXONOMY, BottleneckCandidate
from app.services.identity.bottleneck_v0 import diagnose_bottleneck_v0
from app.services.identity.scoring.gap import CreateConsumeResult, GapResult


def _validate_bottleneck_response(raw: object) -> list:
    """B4 (docs/work.md): raises on a malformed LLM response so
    generate_structured_with_repair() knows to retry once before this
    function falls back to the deterministic v0 diagnosis. Accepts
    either a bare array or {'candidates': [...]}, matching what the
    caller already tolerated."""
    candidates = raw if isinstance(raw, list) else (raw.get("candidates") if isinstance(raw, dict) else None)
    if not isinstance(candidates, list) or not candidates:
        raise ValueError("response must be a non-empty array of bottleneck candidates")
    return candidates


def diagnose_bottleneck_v1(
    gap_result: GapResult,
    create_consume: CreateConsumeResult,
    consistency: float,
    events: List[EvidenceEvent],
    llm_provider: Optional[Any] = None,
    user_id: str = "demo_user",
) -> List[BottleneckCandidate]:
    """Diagnoses Potential Bottleneck candidates using LLMProvider facade with fallback to v0."""
    if not llm_provider or not hasattr(llm_provider, "generate_structured"):
        return diagnose_bottleneck_v0(gap_result, create_consume, consistency, events)

    try:
        # Build deterministic inputs for LLM prompt
        attr_deficits = [
            {"attr_id": a.attr_id, "deficit": round(a.deficit, 3), "creation_contrib": round(a.creation_contrib, 3)}
            for a in gap_result.per_attribute
        ]
        
        evidence_summary = {
            "total_events": len(events),
            "drift_event_count": len([e for e in events if e.category == "focus_drift"]),
            "creation_event_count": len([e for e in events if e.category == "creation"]),
            "passive_event_count": len([e for e in events if e.category == "passive_learning"]),
        }

        # Format prompt template
        prompt_text = load_prompt("identity/bottleneck_diagnosis_v1.md")
        formatted_prompt = prompt_text.format(
            attribute_deficits_json=json.dumps(attr_deficits),
            evidence_aggregates_json=json.dumps(evidence_summary),
            create_consume_ratio=round(create_consume.ratio, 2),
            consistency_score=round(consistency, 2),
        )

        messages = [
            {"role": "system", "content": "You are the Trellis Identity Modeler. Return structured JSON matching BottleneckCandidate array."},
            {"role": "user", "content": formatted_prompt},
        ]

        # Call LLMProvider facade
        schema = {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "label": {"type": "string"},
                    "confidence": {"type": "number"},
                    "supporting_evidence_ids": {"type": "array", "items": {"type": "string"}},
                    "missing_evidence_ids": {"type": "array", "items": {"type": "string"}},
                    "alternative": {"type": "string"},
                },
                "required": ["label", "confidence"],
            },
        }

        raw_candidates = generate_structured_with_repair(
            llm_provider, schema, messages, _validate_bottleneck_response
        )

        parsed_candidates: List[BottleneckCandidate] = []
        for item in raw_candidates:
            if not isinstance(item, dict):
                continue
            label = str(item.get("label", "")).lower()
            if label not in BOTTLENECK_TAXONOMY:
                continue
            
            conf = float(item.get("confidence", 0.70))
            conf = max(0.0, min(1.0, conf))
            
            supp = [str(x) for x in item.get("supporting_evidence_ids", []) if isinstance(x, (str, int))]
            miss = [str(x) for x in item.get("missing_evidence_ids", []) if isinstance(x, (str, int))]
            alt = str(item.get("alternative")) if item.get("alternative") else None

            parsed_candidates.append(
                BottleneckCandidate(
                    label=label,
                    confidence=conf,
                    supporting_evidence_ids=supp,
                    missing_evidence_ids=miss,
                    alternative=alt,
                )
            )

        if parsed_candidates:
            return parsed_candidates[:2]

        return diagnose_bottleneck_v0(gap_result, create_consume, consistency, events)

    except Exception:
        # On any LLM provider failure, safely fall back to heuristic v0
        return diagnose_bottleneck_v0(gap_result, create_consume, consistency, events)
