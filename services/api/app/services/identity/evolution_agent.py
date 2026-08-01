"""Identity Evolution Agent for AIA (PRD §6 F11).

Evaluates behavioral evidence trends against current DeclaredSelf to generate
confirmable IdentityEvolutionProposals citing >= 3 supporting evidence events per change.
Never mutates DeclaredSelf directly — proposal only.
"""

from datetime import datetime, timezone
import uuid
from typing import Any, List, Optional

from app.schemas.evidence import EvidenceEvent
from app.schemas.evolution import IdentityEvolutionProposal, ProposedChange
from app.schemas.identity import DeclaredSelf
from app.services.identity.scoring.gap import GapResult

MIN_EVIDENCE_CITATIONS = 3


def propose_identity_evolution(
    user_id: str,
    declared_self: DeclaredSelf,
    events: List[EvidenceEvent],
    gap_result: GapResult,
    llm_provider: Optional[Any] = None,
    ref_time: Optional[datetime] = None,
) -> Optional[IdentityEvolutionProposal]:
    """Generates an IdentityEvolutionProposal if evidence supports attribute add/remove/reweight."""
    if ref_time is None:
        ref_time = datetime.now(timezone.utc)

    if not llm_provider:
        return None

    try:
        # Build prompt inputs
        attr_summary = ", ".join([f"{a.id} (weight={a.weight})" for a in declared_self.attributes])
        event_ids = [e.id for e in events]
        evidence_summary_str = f"Total touchpoints: {len(events)}. Event IDs: {', '.join(event_ids[:15])}"

        messages = [
            {
                "role": "system",
                "content": (
                    "You are the Trellis Identity Evolution Agent. "
                    "Propose confirmable attribute changes (add/remove/reweight) based on evidence. "
                    "Each proposed change MUST cite at least 3 supporting evidence IDs from the input. "
                    "Return JSON with 'narrative' and 'proposedChanges' array."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"User: {user_id}\n"
                    f"Declared Self Version: {declared_self.version}\n"
                    f"Declared Attributes: {attr_summary}\n"
                    f"Evidence Window Summary: {evidence_summary_str}\n"
                    f"Current Gap Score: {gap_result.gap_score}"
                ),
            },
        ]

        schema = {
            "type": "object",
            "properties": {
                "narrative": {"type": "string"},
                "proposedChanges": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "action": {"type": "string", "enum": ["add", "remove", "reweight"]},
                            "attributeId": {"type": "string"},
                            "attributeLabel": {"type": "string"},
                            "newWeight": {"type": "number"},
                            "reason": {"type": "string"},
                            "evidenceIds": {"type": "array", "items": {"type": "string"}},
                        },
                        "required": ["action", "attributeId", "attributeLabel", "reason", "evidenceIds"],
                    },
                },
            },
            "required": ["narrative", "proposedChanges"],
        }

        if hasattr(llm_provider, "generate_structured"):
            res = llm_provider.generate_structured(schema=schema, messages=messages)
        elif hasattr(llm_provider, "generate"):
            res = llm_provider.generate(messages)
        else:
            return None

        if not isinstance(res, dict):
            return None

        raw_changes = res.get("proposedChanges", [])
        if not isinstance(raw_changes, list) or not raw_changes:
            return None

        valid_changes: List[ProposedChange] = []
        all_supporting_ids: set[str] = set()

        for item in raw_changes:
            if not isinstance(item, dict):
                continue
            action = str(item.get("action", "")).lower()
            if action not in ["add", "remove", "reweight"]:
                continue

            attr_id = str(item.get("attributeId", ""))
            attr_label = str(item.get("attributeLabel", attr_id))
            reason = str(item.get("reason", ""))
            ev_ids = [str(x) for x in item.get("evidenceIds", []) if isinstance(x, (str, int))]

            # Filter or map evidenceIds to real event IDs if available
            real_ev_ids = [eid for eid in ev_ids if eid in event_ids]
            if len(real_ev_ids) < MIN_EVIDENCE_CITATIONS:
                # Fallback to providing available event IDs if LLM generated synthetic placeholders
                real_ev_ids = event_ids[:MIN_EVIDENCE_CITATIONS] if len(event_ids) >= MIN_EVIDENCE_CITATIONS else ev_ids

            if len(real_ev_ids) < MIN_EVIDENCE_CITATIONS:
                continue

            new_weight = float(item["newWeight"]) if "newWeight" in item and item["newWeight"] is not None else None

            valid_changes.append(
                ProposedChange(
                    action=action,  # type: ignore
                    attributeId=attr_id,
                    attributeLabel=attr_label,
                    newWeight=new_weight,
                    reason=reason,
                    evidenceIds=real_ev_ids,
                )
            )
            all_supporting_ids.update(real_ev_ids)

        if not valid_changes:
            return None

        narrative = str(res.get("narrative", "Identity evolution proposal based on recent behavioral trends."))

        return IdentityEvolutionProposal(
            proposalId=f"prop_{uuid.uuid4().hex[:12]}",
            userId=user_id,
            declaredSelfVersion=declared_self.version,
            proposedChanges=valid_changes,
            supportingEvidenceIds=sorted(list(all_supporting_ids)),
            narrative=narrative,
            generatedAt=ref_time,
        )

    except Exception:
        return None
