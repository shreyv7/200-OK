from __future__ import annotations

from typing import Any

from app.providers.llm.base import LLMProvider


class FakeLLMProvider(LLMProvider):
  """Deterministic LLM stub for tests and M0 wiring."""

  def __init__(self, response: dict[str, Any] | None = None) -> None:
      self.response = response or {"status": "ok"}
      self.calls: list[dict[str, Any]] = []

  def generate_structured(
      self,
      schema: dict[str, Any],
      messages: list[dict[str, str]],
      opts: dict[str, Any] | None = None,
  ) -> dict[str, Any]:
      self.calls.append(
          {"schema": schema, "messages": messages, "opts": opts or {}}
      )
      return dict(self.response)
