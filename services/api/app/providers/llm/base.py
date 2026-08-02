from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class LLMUsage:
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None


class LLMProviderUnavailable(Exception):
    """Raised when an underlying LLM provider service or key pool is exhausted/unavailable."""


class LLMProvider(ABC):
    """Model-agnostic structured generation facade (techstack §11.1)."""

    last_usage: LLMUsage | None = None

    @abstractmethod
    def generate_structured(
        self,
        schema: dict[str, Any],
        messages: list[dict[str, str]],
        opts: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Return JSON-compatible structured output validated against schema."""
