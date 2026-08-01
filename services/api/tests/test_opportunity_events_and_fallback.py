from __future__ import annotations

from app.providers.search.base import Document
from app.providers.search.fake import FakeSearchProvider
from app.services.recommendation.catalog import FixtureCatalogSource
from app.services.recommendation.curation_cycle import run_curation_cycle
from tests.fixtures.sample_data import sample_decision_packet_with_stage


class RaisingSearchProvider(FakeSearchProvider):
    def search(self, query: str, opts=None):  # type: ignore[no-untyped-def]
        raise TimeoutError("search down")


def test_opportunity_live_badge_when_search_succeeds() -> None:
    packet = sample_decision_packet_with_stage()
    search = FakeSearchProvider(
        documents=[
            Document(
                title="Pune speaking workshop",
                url="https://example.com/workshop",
                extract="Local workshop",
                source="live_web",
            )
        ]
    )
    stack = run_curation_cycle(
        packet,
        run_id="run-opp-live",
        search=search,
        persist_active_stack=False,
        include_p1_lenses=True,
        catalog_source=FixtureCatalogSource(),
    )
    events = [element for element in stack.elements if element.type == "real_world_experience"]
    assert events
    assert events[0].sourceBadge in {"Live web", "Cached web"}


def test_opportunity_pune_fallback_on_failure() -> None:
    packet = sample_decision_packet_with_stage()
    stack = run_curation_cycle(
        packet,
        run_id="run-opp-fallback",
        search=RaisingSearchProvider(),
        persist_active_stack=False,
        include_p1_lenses=True,
        catalog_source=FixtureCatalogSource(),
    )
    events = [element for element in stack.elements if element.type == "real_world_experience"]
    assert events
    assert events[0].sourceBadge == "Curated fallback"
