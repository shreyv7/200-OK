"""B6 (docs/work.md) regression test: diagnose_bottleneck_v1's real LLM
path now actually completes, instead of always silently crashing into
the v0 fallback (see loader.py's module docstring for the two bugs
found: wrong prompt filename, then a str.format()/JSON-example
collision). tests/identity/test_m4_bottleneck.py's existing "llm_path"
test doesn't catch this — it uses FakeLLMProvider()'s default
{"status": "ok"} response, which fails validation and falls back to v0
regardless of whether the prompt rendering step itself works."""

from __future__ import annotations

from app.providers.llm.fake import FakeLLMProvider
from app.services.identity.bottleneck_v1 import diagnose_bottleneck_v1
from app.services.identity.scoring.gap import CreateConsumeResult
from tests.fixtures.aarav_seed import generate_aarav_seed_events, get_aarav_declared_self
from app.services.identity.recompute import recompute_user_gap


def test_llm_path_actually_executes_and_is_not_a_silent_v0_fallback() -> None:
    declared = get_aarav_declared_self()
    events = generate_aarav_seed_events()
    gap_result, _, _ = recompute_user_gap("aarav_demo", declared, events)
    create_consume = CreateConsumeResult(create_points=10.0, consume_points=5.0, drift_points=1.0, ratio=1.5)

    # A confidence value v0's fixed heuristic rules never produce (v0 only
    # ever emits 0.85 / 0.75 / 0.70 / 0.60) proves this response came from
    # the LLM path, not a silently-triggered fallback.
    # FakeLLMProvider.generate_structured() does dict(self.response), so
    # the response must be a mapping -- {"candidates": [...]} is the
    # dict-shaped alternative _validate_bottleneck_response() accepts.
    fake = FakeLLMProvider(
        response={
            "candidates": [
                {
                    "label": "networking",
                    "confidence": 0.42,
                    "supporting_evidence_ids": ["evt_1"],
                    "missing_evidence_ids": [],
                    "alternative": "focus",
                }
            ]
        }
    )

    candidates = diagnose_bottleneck_v1(
        gap_result, create_consume, 0.5, events, llm_provider=fake, user_id="aarav_demo"
    )

    assert len(fake.calls) == 1  # succeeded on the first attempt, no repair retry needed
    assert len(candidates) == 1
    assert candidates[0].label == "networking"
    assert candidates[0].confidence == 0.42
