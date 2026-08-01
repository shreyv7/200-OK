"""Unit tests for AIA Milestone M6 (CatalogFeatures Enrichment & Embedding Trigger).

Validates stage tier derivation from Gap score, bottleneck label pass-through, top deficit attribute
extraction, graceful embedding provider bypass, and DecisionPacket catalog_features payload.
Runs natively via python -m unittest / pytest.
"""

from datetime import datetime, timezone
import unittest

from app.services.decision.packet import BottleneckCandidate
from app.services.identity.catalog_features import (
    extract_catalog_features,
    get_stage_from_gap,
    trigger_identity_embedding,
)
from app.services.identity.recompute import recompute_user_gap
from tests.fixtures.aarav_seed import (
    generate_aarav_seed_events,
    get_aarav_declared_self,
)


class FakeEmbeddingProvider:
    """Fake embedding provider for test suite."""

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [[0.1, 0.2, 0.3, 0.4] for _ in texts]


class TestM6CatalogFeatures(unittest.TestCase):

    def test_stage_tier_mapping(self):
        """Test 1: Gap scores map deterministically to peak, advancing, developing, early stage tiers."""
        self.assertEqual(get_stage_from_gap(10), "peak")
        self.assertEqual(get_stage_from_gap(25), "peak")
        self.assertEqual(get_stage_from_gap(35), "advancing")
        self.assertEqual(get_stage_from_gap(50), "advancing")
        self.assertEqual(get_stage_from_gap(60), "developing")
        self.assertEqual(get_stage_from_gap(75), "developing")
        self.assertEqual(get_stage_from_gap(85), "early")
        self.assertEqual(get_stage_from_gap(100), "early")

    def test_bottleneck_label_passthrough(self):
        """Test 2: Top bottleneck candidate label and confidence are passed through to catalog_features."""
        gap_res, _, _ = recompute_user_gap("aarav_demo", get_aarav_declared_self(), [])
        candidates = [BottleneckCandidate(label="execution", confidence=0.85)]

        features = extract_catalog_features(gap_res, candidates)
        self.assertEqual(features.bottleneck_label, "execution")
        self.assertEqual(features.bottleneck_confidence, 0.85)

    def test_top_deficit_attr_derivation(self):
        """Test 3: Attribute with highest deficit is correctly identified."""
        gap_res, _, _ = recompute_user_gap("aarav_demo", get_aarav_declared_self(), [])
        features = extract_catalog_features(gap_res)

        self.assertTrue(len(features.top_deficit_attr_id) > 0)
        worst_attr = max(gap_res.per_attribute, key=lambda a: a.deficit)
        self.assertEqual(features.top_deficit_attr_id, worst_attr.attr_id)

    def test_empty_candidates_fallback(self):
        """Test 4: Empty bottleneck candidates result in empty bottleneck_label and 0.0 confidence."""
        gap_res, _, _ = recompute_user_gap("aarav_demo", get_aarav_declared_self(), [])
        features = extract_catalog_features(gap_res, bottleneck_candidates=[])

        self.assertEqual(features.bottleneck_label, "")
        self.assertEqual(features.bottleneck_confidence, 0.0)

    def test_embedding_trigger_none_provider(self):
        """Test 5: None embedding_provider gracefully returns None without error."""
        aarav_declared = get_aarav_declared_self()
        vec = trigger_identity_embedding(aarav_declared, embedding_provider=None)
        self.assertIsNone(vec)

    def test_embedding_trigger_live_provider(self):
        """Test 6: FakeEmbeddingProvider returns expected embedding vector."""
        aarav_declared = get_aarav_declared_self()
        fake_provider = FakeEmbeddingProvider()
        vec = trigger_identity_embedding(aarav_declared, embedding_provider=fake_provider)

        self.assertIsNotNone(vec)
        self.assertEqual(len(vec), 4)

    def test_recompute_attaches_catalog_features(self):
        """Test 7: recompute_user_gap attaches catalog_features to DecisionPacket."""
        ref_time = datetime.now(timezone.utc)
        aarav_declared = get_aarav_declared_self()
        seed_events = generate_aarav_seed_events(ref_time=ref_time)

        gap_res, _, packet = recompute_user_gap("aarav_demo", aarav_declared, seed_events, ref_time=ref_time)

        self.assertIsNotNone(packet.catalog_features)
        self.assertIn(packet.catalog_features.stage, ["early", "developing", "advancing", "peak"])


if __name__ == "__main__":
    unittest.main()
