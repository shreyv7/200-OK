"""Rule/heuristic Bottleneck Packet v0 Generator for AIA.

Produces structured BottleneckCandidate list mapping evidence deficits and Create:Consume imbalance
to the BOTTLENECK_TAXONOMY without calling LLMs.
"""

from typing import List
from app.schemas.evidence import EvidenceEvent
from app.services.decision.packet import BottleneckCandidate, BOTTLENECK_TAXONOMY
from app.services.identity.scoring.gap import GapResult, CreateConsumeResult


def diagnose_bottleneck_v0(
    gap_result: GapResult,
    create_consume: CreateConsumeResult,
    consistency: float,
    events: List[EvidenceEvent],
) -> List[BottleneckCandidate]:
    """Diagnoses Potential Bottleneck candidates using deterministic heuristic rules."""
    candidates: List[BottleneckCandidate] = []
    drift_event_ids = [e.id for e in events if e.category == "focus_drift"]

    # Rule 1: High drift or low Create:Consume ratio -> 'execution' or 'focus'
    if create_consume.ratio < 0.5 or create_consume.drift_points > create_consume.create_points:
        candidates.append(
            BottleneckCandidate(
                label="execution",
                confidence=0.85,
                supporting_evidence_ids=drift_event_ids[:3],
                missing_evidence_ids=[],
                alternative="focus",
            )
        )

    # Rule 2: Low consistency score -> 'consistency'
    if consistency < 0.4:
        candidates.append(
            BottleneckCandidate(
                label="consistency",
                confidence=0.75,
                supporting_evidence_ids=[],
                missing_evidence_ids=[],
                alternative="discipline",
            )
        )

    # Rule 3: Largest attribute deficit
    if gap_result.per_attribute:
        worst_attr = max(gap_result.per_attribute, key=lambda a: a.deficit)
        if worst_attr.attr_id == "public_speaker" and worst_attr.deficit > 0.4:
            if not any(c.label == "communication" for c in candidates):
                candidates.append(
                    BottleneckCandidate(
                        label="communication",
                        confidence=0.70,
                        supporting_evidence_ids=[],
                        missing_evidence_ids=[],
                        alternative="confidence",
                    )
                )
        elif worst_attr.attr_id == "builder" and worst_attr.deficit > 0.4:
            if not any(c.label == "execution" for c in candidates):
                candidates.append(
                    BottleneckCandidate(
                        label="execution",
                        confidence=0.70,
                        supporting_evidence_ids=[],
                        missing_evidence_ids=[],
                        alternative="knowledge",
                    )
                )

    # Fallback if no specific rule fired
    if not candidates:
        candidates.append(
            BottleneckCandidate(
                label="execution",
                confidence=0.60,
                supporting_evidence_ids=[],
                missing_evidence_ids=[],
                alternative="consistency",
            )
        )

    # Limit to top 2 candidates max
    return candidates[:2]
