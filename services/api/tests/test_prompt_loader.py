"""B6 (docs/work.md): prompt loading/rendering facade."""

from __future__ import annotations

import pytest

from app.prompts.loader import build_messages, load_prompt, render_prompt


def test_load_prompt_raises_on_missing_file() -> None:
    with pytest.raises(FileNotFoundError):
        load_prompt("identity/does_not_exist_v99")


def test_render_prompt_substitutes_double_brace_placeholders() -> None:
    text = render_prompt("identity/declared_self_extraction_v1", interview_transcript="hi", output_schema_json="{}")
    assert "{{ interview_transcript }}" not in text
    assert "hi" in text


def test_render_prompt_raises_on_missing_value_naming_the_placeholder() -> None:
    with pytest.raises(KeyError, match="interview_transcript"):
        render_prompt("identity/declared_self_extraction_v1", output_schema_json="{}")


def test_build_messages_returns_system_and_user_roles() -> None:
    messages = build_messages(
        "identity/declared_self_extraction_v1", interview_transcript="hi", output_schema_json="{}"
    )
    assert [m["role"] for m in messages] == ["system", "user"]
    assert "JSON" in messages[0]["content"]


def test_bottleneck_diagnosis_template_renders_without_error() -> None:
    """Regression test (B6): this exact rendering used to crash two
    different ways before B6 - load_prompt() was called with the .md
    extension already appended (always FileNotFoundError), and even
    past that, str.format() collided with this template's own "Output
    Format" JSON example (KeyError). Both were invisible because the
    only caller wraps everything in a blanket except-Exception fallback.
    This proves the template actually loads and renders end to end now."""
    text = render_prompt(
        "identity/bottleneck_diagnosis_v1",
        attribute_deficits_json="[]",
        evidence_aggregates_json="{}",
        create_consume_ratio=1.0,
        consistency_score=0.5,
    )
    assert "attribute_deficits_json" not in text
    # the template's own literal JSON example must survive untouched
    assert '"label": "execution"' in text


def test_weekly_report_template_renders_without_error() -> None:
    text = render_prompt(
        "identity/weekly_report_v1",
        user_id="u1",
        gap_start=60,
        gap_end=55,
        gap_delta=-5,
        evidence_summary="- mission_completed (creation)",
    )
    assert "gap_start" not in text
    assert "60" in text


def test_evolution_proposal_template_renders_without_error() -> None:
    text = render_prompt(
        "identity/evolution_proposal_v1",
        user_id="u1",
        declared_self_version=2,
        declared_attributes_summary="public_speaking (weight=0.5)",
        evidence_summary="Total touchpoints: 10.",
        gap_score=42,
    )
    assert "gap_score" not in text
    assert "42" in text
