from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas import StackElement, StackExplanation


def test_stack_element_requires_all_explanations() -> None:
    element = StackElement(
        id="elem-1",
        type="media",
        title="Valid element",
        sourceBadge="Curated fallback",
        explanation=StackExplanation(
            whyThis="Because it matches the bottleneck.",
            whyNow="Because drift was detected.",
            howReducesGap="Because it adds creation evidence.",
        ),
    )
    assert element.explanation.whyThis
    assert element.explanation.whyNow
    assert element.explanation.howReducesGap


@pytest.mark.parametrize("missing_field", ["whyThis", "whyNow", "howReducesGap"])
def test_stack_element_rejects_missing_explanation(missing_field: str) -> None:
    payload = {
        "id": "elem-1",
        "type": "media",
        "title": "Invalid element",
        "sourceBadge": "Curated fallback",
        "explanation": {
            "whyThis": "x",
            "whyNow": "y",
            "howReducesGap": "z",
        },
    }
    payload["explanation"].pop(missing_field)

    with pytest.raises(ValidationError):
        StackElement.model_validate(payload)
