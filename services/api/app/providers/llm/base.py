from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class LLMProviderUnavailable(RuntimeError):
  """Raised when a provider (or its whole key/model pool) cannot currently
  serve a request for a transient reason -- rate limit, quota exhaustion,
  outage. Callers (e.g. FailoverLLMProvider, docs/work.md B3) can catch
  this one generic type to decide whether to retry elsewhere, without
  importing any provider's vendor SDK exception types (techstack §11.1:
  "no feature imports Gemini/Bedrock/Tavily SDKs outside providers/").

  A malformed request (bad schema, invalid input) is NOT this -- it will
  fail identically on every provider, so implementations should let it
  propagate as whatever it naturally is instead of wrapping it here."""


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
