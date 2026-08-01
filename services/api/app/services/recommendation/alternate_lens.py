"""Prepared alternate lens after hypothesis failure — AIS M5."""

from __future__ import annotations

from datetime import datetime, timezone

from app.schemas import IdentityStack, StackElement, StackExplanation
from app.services.recommendation.fallback_catalog import get_fallback_mission
from app.services.recommendation.variants import generate_variants, select_variant_by_intensity


def request_alternate_stack(
    *,
    user_id: str,
    prior_stack: IdentityStack | None,
    failed_lens: str = "media",
    hypothesis_id: str | None = None,
) -> IdentityStack:
    """Swap to Micro-Action lens without blocking on a new LLM."""
    bottleneck = prior_stack.bottleneck if prior_stack is not None else "execution"
    hyp_id = hypothesis_id or (prior_stack.hypothesisId if prior_stack else f"hyp-alt-{user_id}")
    now = datetime.now(timezone.utc)

    mission = get_fallback_mission(bottleneck, small_experiment=True)
    element = StackElement(
        id=mission["id"],
        type="micro_mission",
        title=mission["title"],
        sourceBadge="Curated fallback",
        explanation=StackExplanation(
            whyThis=(
                f"System Unlearning switched away from {failed_lens} after repeated dismissals."
            ),
            whyNow="Prepared micro-action is ready without waiting for new retrieval.",
            howReducesGap="Smallest aligned action rebuilds momentum after a failed hypothesis.",
        ),
    )

    stack = IdentityStack(
        id=f"stack-alt-{user_id}",
        userId=user_id,
        hypothesisId=hyp_id,
        bottleneck=bottleneck,
        elements=[element],
        curatedAt=now,
    )

    micro_variant = select_variant_by_intensity(generate_variants(stack), "micro")
    return micro_variant.stack
