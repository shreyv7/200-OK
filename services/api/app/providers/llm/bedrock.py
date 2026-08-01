"""Amazon Bedrock failover provider (stub). Owner: Backend.

Structurally present per milestones.md M3 ("LLMProvider DI wired ...
Bedrock failover stub") and techstack.md §11.3. Not exercised in the
hackathon build until AWS credentials/testing happen (M8: "Bedrock
failover tested once"). Only file allowed to import boto3.
"""

from __future__ import annotations

from typing import Any

from app.providers.llm.base import LLMProvider


class BedrockLLMProvider(LLMProvider):
    def __init__(self, region: str | None = None, model_id: str | None = None) -> None:
        self._region = region
        self._model_id = model_id

    def generate_structured(
        self,
        schema: dict[str, Any],
        messages: list[dict[str, str]],
        opts: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        raise NotImplementedError(
            "BedrockLLMProvider is an untested failover stub (milestones.md M3/M8) — "
            "not wired to a real boto3 call yet."
        )
