from __future__ import annotations

from datetime import datetime, timezone

from app.agents._contracts import (
  BottleneckPacket,
  DecisionPacket,
  ElementType,
  IdentityStack,
  IdentityStackElement,
  SourceBadge,
)


def sample_decision_packet() -> DecisionPacket:
  return DecisionPacket(
      run_id="run-fixture-001",
      user_id="user-aarav",
      gap_score=68.0,
      gap_delta=1.5,
      invalidate_stack=True,
      bottleneck=BottleneckPacket(
          bottleneck="execution",
          confidence=0.72,
          supporting_evidence=["no publishes in 14 days", "high passive learning"],
          missing_evidence=["public artifact"],
          alternative_bottleneck="confidence",
      ),
      trigger="evidence.created",
  )


def sample_stack_element() -> IdentityStackElement:
  return IdentityStackElement(
      element_id="elem-1",
      element_type=ElementType.MEDIA,
      title="Fixture resource",
      url="https://example.com/resource",
      hypothesis_id="hyp-fixture-001",
      source_badge=SourceBadge.CURATED_FALLBACK,
      why_this="Fixture explanation for contract tests.",
      why_now="Fixture timing context.",
      how_reduces_gap="Fixture gap impact statement.",
      simulated=True,
  )


def sample_identity_stack() -> IdentityStack:
  element = sample_stack_element()
  return IdentityStack(
      stack_id="stack-fixture-001",
      hypothesis_id="hyp-fixture-001",
      curated_at=datetime.now(timezone.utc),
      elements=[element],
      simulated=True,
  )


def sample_coordinator_state() -> dict:
  packet = sample_decision_packet()
  return {
      "trigger": packet.trigger,
      "run_id": packet.run_id,
      "user_id": packet.user_id,
      "decision_packet": packet.model_dump(),
      "stack_draft": None,
      "visited": [],
  }
