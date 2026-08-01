from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class LLMUsage:
  """Best-effort token usage for one generate_structured() call
  (docs/work.md B5). Not every provider can report this -- FakeLLMProvider
  never sets it, since a fake call costs nothing."""

  input_tokens: int | None = None
  output_tokens: int | None = None
  total_tokens: int | None = None


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

  #: Set by an implementation after a successful call, when it can report
  #: real usage (docs/work.md B5). None means "unknown/not applicable",
  #: not "zero" -- callers should treat None as no cost data, not free.
  last_usage: LLMUsage | None = None

  @abstractmethod
  def generate_structured(
      self,
      schema: dict[str, Any],
      messages: list[dict[str, str]],
      opts: dict[str, Any] | None = None,
  ) -> dict[str, Any]:
      """Return JSON-compatible structured output validated against schema."""
