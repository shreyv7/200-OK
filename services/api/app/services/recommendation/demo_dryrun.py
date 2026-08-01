"""Full continuous-loop dry-run against the demo script — AIS M8."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.schemas import BottleneckPacket, DecisionPacket
from app.services.recommendation.guardian import GuardianContext, evaluate_guardian
from app.services.recommendation.intervention_action import on_intervention_action
from app.services.recommendation.ledger_intake import clear_intake_store
from app.services.recommendation.outcome_window import clear_outcome_store
from app.services.recommendation.prepared_intervention import prepare_doomscroll_intervention
from app.services.recommendation.stack_state import clear_stack_state, set_active_stack
from app.services.recommendation.variants import select_variant_by_capacity

DEMO_HYPOTHESIS_FAMILY = "media_public_speaking"
MICRO_ACTION_FAMILY = "micro_action_rehearsal"


def _demo_packet(user_id: str) -> DecisionPacket:
    return DecisionPacket(
        userId=user_id,
        gapDelta=1.5,
        invalidateStack=True,
        invalidatedElementIds=[],
        bottleneck=BottleneckPacket(
            bottleneck="execution",
            confidence=0.72,
            supporting_evidence=["fixture evidence"],
            missing_evidence=[],
            alternative_bottleneck="confidence",
        ),
        rankingFeatures={},
    )


@dataclass
class DemoDryRunTrace:
    beats: list[dict[str, Any]] = field(default_factory=list)

    def record(self, beat: str, **payload: Any) -> None:
        self.beats.append({"beat": beat, **payload})


def run_demo_dryrun(*, user_id: str = "user-aarav") -> DemoDryRunTrace:
    """Observe → curate → guardian → capacity swap → dismiss/unlearn → complete."""
    clear_stack_state()
    clear_intake_store()
    clear_outcome_store()

    trace = DemoDryRunTrace()
    packet = _demo_packet(user_id)

    prepared = prepare_doomscroll_intervention(user_id, decision_packet=packet, run_id=f"dryrun-{user_id}")
    set_active_stack(user_id, prepared.stack)
    trace.record(
        "beat1_mirror",
        stack_id=prepared.stack.id,
        element_count=len(prepared.stack.elements),
        honesty_badges=[element.sourceBadge for element in prepared.stack.elements],
    )

    guardian_full = evaluate_guardian(GuardianContext(capacity_pct=80))
    guardian_low = evaluate_guardian(GuardianContext(capacity_pct=20))
    low_capacity_stack = select_variant_by_capacity(prepared.variants, 20).stack
    trace.record(
        "beat3_protection",
        full_intensity=guardian_full.intensity,
        low_capacity_intensity=guardian_low.intensity,
        swapped_element_count=len(low_capacity_stack.elements),
        guardian_reason=guardian_low.reason,
    )

    hypothesis_id = prepared.stack.hypothesisId
    for index in range(3):
        outcome = on_intervention_action(
            user_id,
            hypothesis_id,
            DEMO_HYPOTHESIS_FAMILY,
            "dismissed",
        )
        trace.record(
            "beat2_dismissal",
            index=index + 1,
            unlearning_triggered=outcome.ledger_entry.unlearningTriggered,
            verdict=outcome.ledger_entry.verdict,
        )

    set_active_stack(user_id, prepared.alternate_stack)
    on_intervention_action(user_id, hypothesis_id, MICRO_ACTION_FAMILY, "delivered")
    completion = on_intervention_action(
        user_id,
        hypothesis_id,
        MICRO_ACTION_FAMILY,
        "completed",
    )
    trace.record(
        "beat4_proof",
        completion_verdict=completion.ledger_entry.verdict,
        alternate_stack_id=(
            completion.alternate_stack.id if completion.alternate_stack is not None else prepared.alternate_stack.id
        ),
        prepared_alternate_ready=prepared.alternate_stack is not None,
    )

    assert prepared.stack.elements, "beat1 stack must not be empty"
    assert prepared.alternate_stack.elements, "prepared alternate must not be empty"
    assert low_capacity_stack.elements, "capacity swap must not be empty"
    return trace
