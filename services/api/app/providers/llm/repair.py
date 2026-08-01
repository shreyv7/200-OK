"""Shared repair-retry helper for generate_structured() call sites.
Owner: Backend. docs/work.md B4.

Real LLM output can be malformed relative to a caller's actual needs
(wrong shape, missing keys, hallucinated references) even when the
provider honored the JSON schema syntactically — a schema constrains
structure, not semantic correctness. This retries once with a corrective
follow-up message before giving up, matching the pattern already proven
in app/services/identity/onboarding_orchestration.py's
`_extract_attributes` (B1).

LLMProviderUnavailable (app/providers/llm/base.py) is deliberately NOT
caught/retried here: by the time a provider raises it, it has already
exhausted its own retry surface (key rotation across a pool in B2,
Bedrock failover in B3). A third retry from this layer would just wait
for another guaranteed-transient failure and add latency for nothing —
it propagates immediately so the caller can fall back to its own
deterministic path (v0 heuristic, cached report, etc.) without delay.
"""

from __future__ import annotations

from typing import Any, Callable, TypeVar

from app.providers.llm.base import LLMProvider

T = TypeVar("T")


def generate_structured_with_repair(
    llm_provider: LLMProvider,
    schema: dict[str, Any],
    messages: list[dict[str, str]],
    validate: Callable[[Any], T],
) -> T:
    """Calls generate_structured(), passes the raw result through
    `validate` (which must raise on invalid input and otherwise return
    the caller's desired shape). On a validation failure, retries once
    with a corrective follow-up message. Any exception from the retry —
    including a second validation failure or a provider-level failure —
    propagates to the caller."""
    raw = llm_provider.generate_structured(schema=schema, messages=messages)
    try:
        return validate(raw)
    except Exception as first_error:
        retry_messages = [
            *messages,
            {
                "role": "user",
                "content": (
                    f"Your previous output was invalid: {first_error}. "
                    "Return valid JSON matching the schema exactly."
                ),
            },
        ]
        raw_retry = llm_provider.generate_structured(schema=schema, messages=retry_messages)
        return validate(raw_retry)
