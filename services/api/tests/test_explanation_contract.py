from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.agents._contracts import ElementType, IdentityStackElement, SourceBadge


def test_identity_stack_element_requires_all_explanations() -> None:
  element = IdentityStackElement(
      element_id="elem-1",
      element_type=ElementType.MEDIA,
      title="Valid element",
      hypothesis_id="hyp-1",
      source_badge=SourceBadge.CURATED_FALLBACK,
      why_this="Because it matches the bottleneck.",
      why_now="Because drift was detected.",
      how_reduces_gap="Because it adds creation evidence.",
  )
  assert element.why_this
  assert element.why_now
  assert element.how_reduces_gap


@pytest.mark.parametrize("missing_field", ["why_this", "why_now", "how_reduces_gap"])
def test_identity_stack_element_rejects_missing_explanation(missing_field: str) -> None:
  payload = {
      "element_id": "elem-1",
      "element_type": "media",
      "title": "Invalid element",
      "hypothesis_id": "hyp-1",
      "source_badge": "curated_fallback",
      "why_this": "x",
      "why_now": "y",
      "how_reduces_gap": "z",
  }
  payload.pop(missing_field)

  with pytest.raises(ValidationError):
      IdentityStackElement.model_validate(payload)
