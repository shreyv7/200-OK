from __future__ import annotations

from app.services.recommendation.catalog import FixtureCatalogSource
from app.services.recommendation.curation_cycle import run_curation_cycle
from tests.fixtures.sample_data import sample_decision_packet_with_stage


def test_run_curation_cycle_includes_catalog_element() -> None:
    packet = sample_decision_packet_with_stage()
    stack = run_curation_cycle(
        packet,
        run_id="run-m6-catalog",
        persist_active_stack=False,
        catalog_source=FixtureCatalogSource(),
        include_p1_lenses=True,
    )
    catalog_types = {"growth_story", "tool", "mentor", "real_world_experience"}
    matched = [element for element in stack.elements if element.type in catalog_types]
    assert matched
    assert "execution" in matched[0].explanation.whyThis
    assert len(stack.elements) <= 4
