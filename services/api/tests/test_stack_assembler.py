from __future__ import annotations

from pathlib import Path

import pytest

from app.providers.llm.fake import FakeLLMProvider
from app.providers.search.fake import FakeSearchProvider
from app.services.recommendation.stack_assembler import assemble_stack
from tests.fixtures.sample_data import sample_decision_packet


def test_assemble_stack_returns_valid_non_empty_stack() -> None:
  packet = sample_decision_packet()
  stack = assemble_stack(
      packet,
      candidates=[],
      capacity_tier="light",
      ledger_weights={"media": 0.6},
      llm=FakeLLMProvider(),
      search=FakeSearchProvider(),
  )

  assert len(stack.elements) >= 1
  assert all(e.why_this and e.why_now and e.how_reduces_gap for e in stack.elements)
  assert stack.hypothesis_id.startswith("hyp-")
  assert stack.invalidate is True


def test_prompt_loader_loads_curator_and_reflect_templates() -> None:
  from app.prompts.loader import load_prompt

  bottleneck = load_prompt("curator_bottleneck")
  next_step = load_prompt("curator_next_step")
  reflect = load_prompt("reflect_verdict")

  assert "bottleneck" in bottleneck
  assert "why_this" in next_step
  assert "verdict" in reflect
