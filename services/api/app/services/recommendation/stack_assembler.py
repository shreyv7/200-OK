from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.agents._contracts import (
  DecisionPacket,
  ElementType,
  IdentityStack,
  IdentityStackElement,
  SourceBadge,
)
from app.providers.llm.fake import FakeLLMProvider
from app.providers.llm.base import LLMProvider
from app.providers.search.fake import FakeSearchProvider
from app.providers.search.base import SearchProvider


def build_providers(
  llm: LLMProvider | None = None,
  search: SearchProvider | None = None,
) -> tuple[LLMProvider, SearchProvider]:
  """Factory seam for DI; Backend Depends() will inject real providers in M3+."""
  return llm or FakeLLMProvider(), search or FakeSearchProvider()


def assemble_stack(
  decision_packet: DecisionPacket,
  candidates: list[dict[str, Any]] | None = None,
  capacity_tier: str = "full",
  ledger_weights: dict[str, float] | None = None,
  *,
  llm: LLMProvider | None = None,
  search: SearchProvider | None = None,
) -> IdentityStack:
  """Assemble the smallest coherent Identity Stack for the current bottleneck.

  M0 returns a fixture-valid stack. M4+ will retrieve, rank, and explain.
  Never returns an empty stack — falls back to curated fixture elements.
  """
  _llm, _search = build_providers(llm, search)
  _ = (_llm, _search, candidates, capacity_tier, ledger_weights)

  hypothesis_id = f"hyp-{decision_packet.run_id}"
  now = datetime.now(timezone.utc)

  elements = [
      IdentityStackElement(
          element_id="elem-action-1",
          element_type=ElementType.MICRO_MISSION,
          title="Ship a 60-second speaking clip",
          hypothesis_id=hypothesis_id,
          source_badge=SourceBadge.CURATED_FALLBACK,
          why_this="Targets the execution bottleneck with the smallest publishable action.",
          why_now="Gap invalidation or drift trigger requested a refreshed stack.",
          how_reduces_gap="Creation evidence raises Revealed Self toward the declared speaker target.",
          simulated=True,
      ),
      IdentityStackElement(
          element_id="elem-resource-1",
          element_type=ElementType.MEDIA,
          title="How to structure a one-minute talk",
          url="https://example.com/one-minute-talk",
          hypothesis_id=hypothesis_id,
          source_badge=SourceBadge.CURATED_FALLBACK,
          why_this="Supports the micro-mission with a concrete structure.",
          why_now="Paired with the action while capacity tier is "
          f"{capacity_tier}.",
          how_reduces_gap="Passive learning plus immediate application closes the say-do gap.",
          simulated=True,
      ),
  ]

  return IdentityStack(
      stack_id=f"stack-{decision_packet.run_id}",
      hypothesis_id=hypothesis_id,
      curated_at=now,
      elements=elements,
      invalidate=decision_packet.invalidate_stack,
      simulated=True,
  )
