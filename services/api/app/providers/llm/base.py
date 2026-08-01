from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class LLMProvider(ABC):
  """Model-agnostic structured generation facade (techstack §11.1)."""

  @abstractmethod
  def generate_structured(
      self,
      schema: dict[str, Any],
      messages: list[dict[str, str]],
      opts: dict[str, Any] | None = None,
  ) -> dict[str, Any]:
      """Return JSON-compatible structured output validated against schema."""
