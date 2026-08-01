"""Token and Cost Metrics tracker. Owner: Backend (Task C6).

Tracks LLM token usage and retrieval provider costs per user.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

_prompt_tokens: dict[str, int] = defaultdict(int)
_completion_tokens: dict[str, int] = defaultdict(int)
_search_calls: dict[str, int] = defaultdict(int)

# Estimated cost constants per 1,000 tokens / 1,000 calls
COST_PER_1K_PROMPT_TOKENS = 0.00015
COST_PER_1K_COMPLETION_TOKENS = 0.00060
COST_PER_SEARCH_CALL = 0.002


def record_llm_usage(user_id: str, prompt_tokens: int, completion_tokens: int) -> None:
    _prompt_tokens[user_id] += prompt_tokens
    _completion_tokens[user_id] += completion_tokens


def record_search_usage(user_id: str, calls: int = 1) -> None:
    _search_calls[user_id] += calls


def get_metrics_summary(user_id: str | None = None) -> dict[str, Any]:
    if user_id is not None:
        p_tok = _prompt_tokens.get(user_id, 0)
        c_tok = _completion_tokens.get(user_id, 0)
        searches = _search_calls.get(user_id, 0)
        estimated_cost = (
            (p_tok / 1000.0) * COST_PER_1K_PROMPT_TOKENS
            + (c_tok / 1000.0) * COST_PER_1K_COMPLETION_TOKENS
            + searches * COST_PER_SEARCH_CALL
        )
        return {
            "user_id": user_id,
            "prompt_tokens": p_tok,
            "completion_tokens": c_tok,
            "total_tokens": p_tok + c_tok,
            "search_calls": searches,
            "estimated_cost_usd": round(estimated_cost, 6),
        }

    total_p = sum(_prompt_tokens.values())
    total_c = sum(_completion_tokens.values())
    total_searches = sum(_search_calls.values())
    total_cost = (
        (total_p / 1000.0) * COST_PER_1K_PROMPT_TOKENS
        + (total_c / 1000.0) * COST_PER_1K_COMPLETION_TOKENS
        + total_searches * COST_PER_SEARCH_CALL
    )
    return {
        "users_count": len(_prompt_tokens),
        "total_prompt_tokens": total_p,
        "total_completion_tokens": total_c,
        "total_tokens": total_p + total_c,
        "total_search_calls": total_searches,
        "total_estimated_cost_usd": round(total_cost, 6),
    }


def reset_metrics() -> None:
    _prompt_tokens.clear()
    _completion_tokens.clear()
    _search_calls.clear()
