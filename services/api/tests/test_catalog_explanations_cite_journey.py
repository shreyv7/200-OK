from __future__ import annotations

from app.services.recommendation.catalog import FixtureCatalogSource
from app.services.recommendation.explanations import build_catalog_explanation
from app.services.recommendation.stack_assembler import assemble_identity_stack
from tests.fixtures.sample_data import sample_decision_packet_with_stage


def test_catalog_explanation_cites_bottleneck_journey() -> None:
    explanation = build_catalog_explanation(
        bottleneck="execution",
        element_type="growth_story",
        title="From draft to stage",
        source_badge="Curated fallback",
        tags={"bottleneck": "execution", "stage": "early", "outcome": "published_first_talk"},
    )
    assert "execution" in explanation.whyThis
    assert "bottleneck" in explanation.whyThis.lower()


def test_stack_catalog_element_has_journey_explanation() -> None:
    packet = sample_decision_packet_with_stage()
    stack = assemble_identity_stack(
        packet,
        knowledge_candidates=[],
        planner_candidates=[],
        catalog_source=FixtureCatalogSource(),
        stage="early",
    )
    catalog_elements = [
        element
        for element in stack.elements
        if element.type in {"growth_story", "tool", "mentor", "real_world_experience"}
    ]
    assert catalog_elements
    assert "execution" in catalog_elements[0].explanation.whyThis
