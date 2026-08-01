from __future__ import annotations

from app.services.recommendation.catalog import FixtureCatalogSource
from app.services.recommendation.stack_assembler import assemble_identity_stack
from tests.fixtures.sample_data import (
    sample_decision_packet_with_bottleneck,
    sample_decision_packet_with_stage,
    sample_offbottleneck_catalog,
)


def test_offbottleneck_catalog_not_included() -> None:
    packet = sample_decision_packet_with_stage()
    stack = assemble_identity_stack(
        packet,
        knowledge_candidates=[],
        planner_candidates=[],
        catalog_source=FixtureCatalogSource(items=sample_offbottleneck_catalog()),
        stage="early",
    )
    types = {element.type for element in stack.elements}
    assert "growth_story" not in types
    assert "tool" not in types
    assert "mentor" not in types


def test_matching_catalog_included() -> None:
    packet = sample_decision_packet_with_stage()
    stack = assemble_identity_stack(
        packet,
        knowledge_candidates=[],
        planner_candidates=[],
        catalog_source=FixtureCatalogSource(),
        stage="early",
    )
    types = {element.type for element in stack.elements}
    assert types.intersection({"growth_story", "tool", "mentor"})
