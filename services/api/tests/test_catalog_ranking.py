from __future__ import annotations

from app.services.recommendation.catalog import CatalogItem
from app.services.recommendation.catalog_ranking import rank_catalog_items, select_catalog_element


def test_bottleneck_match_outranks_popularity() -> None:
    items = [
        CatalogItem(
            id="popular-off",
            type="growth_story",
            title="Viral motivation",
            tags={"bottleneck": "discipline", "stage": "late"},
            popularity=100000.0,
        ),
        CatalogItem(
            id="matched",
            type="growth_story",
            title="Shipping story",
            tags={"bottleneck": "execution", "stage": "early"},
            popularity=1.0,
        ),
    ]
    ranked = rank_catalog_items(items, bottleneck="execution", stage="early")
    assert ranked[0].item.id == "matched"


def test_ranking_is_deterministic() -> None:
    items = [
        CatalogItem(id="b", type="tool", title="B", tags={"bottleneck": "execution", "stage": "early"}),
        CatalogItem(id="a", type="tool", title="A", tags={"bottleneck": "execution", "stage": "early"}),
    ]
    first = rank_catalog_items(items, bottleneck="execution", stage="early")
    second = rank_catalog_items(items, bottleneck="execution", stage="early")
    assert [row.item.id for row in first] == [row.item.id for row in second]


def test_select_requires_exact_bottleneck_match() -> None:
    items = [
        CatalogItem(id="off", type="tool", title="Off", tags={"bottleneck": "discipline", "stage": "early"}),
    ]
    ranked = rank_catalog_items(items, bottleneck="execution", stage="early")
    assert select_catalog_element(ranked) is None
