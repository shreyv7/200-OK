from __future__ import annotations

from datetime import datetime, timezone

from app.schemas import (
    BottleneckPacket,
    DecisionPacket,
    EvidenceEvent,
    IdentityStack,
    StackElement,
    StackExplanation,
)


def sample_decision_packet() -> DecisionPacket:
    return DecisionPacket(
        userId="user-aarav",
        gapDelta=1.5,
        invalidateStack=True,
        invalidatedElementIds=[],
        bottleneck=BottleneckPacket(
            bottleneck="execution",
            confidence=0.72,
            supporting_evidence=["no publishes in 14 days", "high passive learning"],
            missing_evidence=["public artifact"],
            alternative_bottleneck="confidence",
        ),
        rankingFeatures={},
    )


def sample_stack_element() -> StackElement:
    return StackElement(
        id="elem-1",
        type="media",
        title="Fixture resource",
        url="https://example.com/resource",
        sourceBadge="Curated fallback",
        explanation=StackExplanation(
            whyThis="Fixture explanation for contract tests.",
            whyNow="Fixture timing context.",
            howReducesGap="Fixture gap impact statement.",
        ),
    )


def sample_identity_stack() -> IdentityStack:
    element = sample_stack_element()
    return IdentityStack(
        id="stack-fixture-001",
        userId="user-aarav",
        hypothesisId="hyp-fixture-001",
        bottleneck="execution",
        elements=[element],
        curatedAt=datetime.now(timezone.utc),
    )


def sample_evidence_event() -> EvidenceEvent:
    return EvidenceEvent(
        id="ev-fixture-001",
        userId="user-aarav",
        timestamp=datetime.now(timezone.utc),
        source="trellis",
        type="mission_completed",
        category="creation",
        identityAttributeIds=["attr-public-speaker"],
        value=1.0,
        baseWeight=3.0,
        metadata={},
        simulated=True,
    )


def sample_coordinator_state() -> dict:
    packet = sample_decision_packet()
    return {
        "trigger": "manual",
        "run_id": "run-fixture-001",
        "user_id": packet.userId,
        "decision_packet": packet.model_dump(),
        "stack_draft": None,
        "visited": [],
        "evidence_id": None,
        "hypothesis_id": "hyp-fixture-001",
    }


def sample_gap_snapshot(*, gap_delta: float = 6.0, gap_score: int = 68) -> "GapSnapshot":
    from app.services.recommendation.gap_snapshot import GapSnapshot

    prior = int(gap_score - gap_delta)
    return GapSnapshot(
        userId="user-aarav",
        gapScore=gap_score,
        gapDelta=gap_delta,
        alignment=100 - gap_score,
        createConsumeRatio=0.42,
        consistency=0.55,
        momentum=-2.0,
        timestamp="2026-08-01T00:00:00Z",
        priorGapScore=prior,
    )


def sample_onboarding_confirm_event(
    *,
    with_gap_snapshot: bool = True,
    twin_version: int = 1,
) -> "OnboardingConfirmEvent":
    from app.services.recommendation.onboarding_trigger import OnboardingConfirmEvent

    return OnboardingConfirmEvent(
        userId="user-aarav",
        twinVersion=twin_version,
        confirmedAt="2026-08-01T12:00:00Z",
        gapSnapshot=sample_gap_snapshot() if with_gap_snapshot else None,
    )
