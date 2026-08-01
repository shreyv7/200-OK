from datetime import datetime

from app.schemas import (
    AttributeContribution,
    BottleneckPacket,
    DeclaredSelf,
    DecisionPacket,
    EvidenceEvent,
    GapBreakdown,
    IdentityAttribute,
    IdentityStack,
    InterventionVariant,
    LedgerEntry,
    StackElement,
    StackExplanation,
)


def test_evidence_event_roundtrip() -> None:
    event = EvidenceEvent(
        id="e1",
        userId="u1",
        timestamp=datetime.utcnow(),
        source="trellis",
        type="mission_completed",
        category="creation",
        identityAttributeIds=["a1"],
        value=1.0,
        baseWeight=3.0,
        metadata={},
        simulated=True,
    )
    assert EvidenceEvent.model_validate(event.model_dump()) == event


def test_declared_self_roundtrip() -> None:
    twin = DeclaredSelf(
        id="d1",
        userId="u1",
        version=1,
        attributes=[
            IdentityAttribute(id="a1", label="Public Speaker", weight=0.5, targetWeeklyPoints=10.0)
        ],
        createdAt=datetime.utcnow(),
    )
    assert DeclaredSelf.model_validate(twin.model_dump()) == twin


def test_gap_breakdown_roundtrip() -> None:
    gap = GapBreakdown(
        userId="u1",
        gapScore=68.0,
        alignmentScore=32.0,
        createPoints=5.0,
        consumePoints=2.0,
        driftPoints=1.0,
        createConsumeRatio=1.6,
        consistency=0.7,
        momentum=-3.0,
        attributes=[AttributeContribution(attributeId="a1", w_i=0.5, D_i=10.0, R_i=4.0, deficit_i=0.6)],
    )
    assert GapBreakdown.model_validate(gap.model_dump()) == gap


def test_bottleneck_and_decision_packet_roundtrip() -> None:
    bottleneck = BottleneckPacket(
        bottleneck="execution",
        confidence=0.8,
        supporting_evidence=["low publish rate"],
        missing_evidence=[],
        alternative_bottleneck="consistency",
    )
    decision = DecisionPacket(userId="u1", gapDelta=-2.0, invalidateStack=True, bottleneck=bottleneck)
    assert DecisionPacket.model_validate(decision.model_dump()) == decision


def test_identity_stack_and_variant_roundtrip() -> None:
    stack = IdentityStack(
        id="s1",
        userId="u1",
        hypothesisId="h1",
        bottleneck="execution",
        elements=[
            StackElement(
                id="el1",
                type="micro_mission",
                title="Record a 60s pitch",
                sourceBadge="Curated fallback",
                explanation=StackExplanation(
                    whyThis="Targets execution bottleneck",
                    whyNow="Gap widened this week",
                    howReducesGap="Adds a creation-weighted event",
                ),
            )
        ],
        curatedAt=datetime.utcnow(),
    )
    variant = InterventionVariant(hypothesisId="h1", intensity="full", stack=stack)
    assert InterventionVariant.model_validate(variant.model_dump()) == variant


def test_ledger_entry_roundtrip() -> None:
    entry = LedgerEntry(
        id="l1",
        userId="u1",
        hypothesisId="h1",
        hypothesisFamily="media_public_speaking",
        action="dismissed",
        verdict="failed",
        timestamp=datetime.utcnow(),
        unlearningTriggered=True,
        lensWeightAdjustment={"media": -0.4},
    )
    assert LedgerEntry.model_validate(entry.model_dump()) == entry
