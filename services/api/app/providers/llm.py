"""LLMProvider interface. Owner: Backend scaffolds; AIA/AIS fill usage patterns.

No Gemini/Bedrock SDK imports here or anywhere outside a future
`providers/llm/` implementation module (hard constraint, guidelines.md §9.3).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class LLMProvider(ABC):
    @abstractmethod
    def generate_structured(
        self,
        schema: dict[str, Any],
        messages: list[dict[str, str]],
        opts: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Return a JSON object validated against `schema`."""
        raise NotImplementedError
