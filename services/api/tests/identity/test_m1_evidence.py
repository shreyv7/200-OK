"""Unit tests for AIA Milestone M1 (Evidence Pipeline + Twin Shell).

Validates event sanitizer, rule-based enrichment, Revealed Self aggregates, and Digital Twin assembly
using the 21-day Aarav seed fixture. Runs natively via python -m unittest.
"""

import unittest

from app.services.identity.sanitizer import validate_and_sanitize_event, SanitizedEvent
from app.services.identity.enrichment import enrich_event
from app.services.identity.aggregates import build_revealed_aggregates
from app.services.identity.twin import assemble_digital_twin
from tests.fixtures.aarav_seed import (
    get_aarav_declared_self,
    generate_aarav_seed_events,
)


class TestM1EvidencePipeline(unittest.TestCase):

    def test_sanitizer_validation(self):
        """Test 1: Sanitizer accepts valid events and rejects corrupt/out-of-bounds payloads."""
        # Valid event
        valid_raw = {
            "user_id": "user_123",
            "event_type": "github_commit",
            "delta_days": 1.5,
            "a_ik": 0.8,
            "simulated": True,
        }
        is_valid, evt, err = validate_and_sanitize_event(valid_raw)
        self.assertTrue(is_valid)
        self.assertIsNotNone(evt)
        self.assertIsNone(err)
        self.assertEqual(evt.event_type, "github_commit")
        self.assertEqual(evt.a_ik, 0.8)

        # Invalid: missing user_id
        is_valid, evt, err = validate_and_sanitize_event({"event_type": "github_commit"})
        self.assertFalse(is_valid)
        self.assertIn("user_id", err)

        # Invalid: negative delta_days
        is_valid, evt, err = validate_and_sanitize_event({
            "user_id": "user_123",
            "event_type": "github_commit",
            "delta_days": -2.0,
        })
        self.assertFalse(is_valid)
        self.assertIn("Negative 'delta_days'", err)

        # Invalid: a_ik out of bounds (> 1.0)
        is_valid, evt, err = validate_and_sanitize_event({
            "user_id": "user_123",
            "event_type": "github_commit",
            "a_ik": 1.5,
        })
        self.assertFalse(is_valid)
        self.assertIn("out of bounds", err)

    def test_enrichment_mapping(self):
        """Test 2: Rule-based enrichment maps keyword content to attribute IDs."""
        unmapped_event = SanitizedEvent(
            event_id="e1",
            user_id="aarav_demo",
            event_type="passive_item",
            attr_id="unmapped",
            a_ik=0.5,
            delta_days=0.0,
            metadata={"title": "Watched 20min speech analysis video"},
        )

        enriched = enrich_event(unmapped_event, known_attribute_ids=["public_speaker", "builder"])
        self.assertEqual(enriched.attr_id, "public_speaker")
        self.assertEqual(enriched.a_ik, 1.0)

        # Explicit attr_id should be preserved
        explicit_event = SanitizedEvent(
            event_id="e2",
            user_id="aarav_demo",
            event_type="github_commit",
            attr_id="builder",
            a_ik=1.0,
            delta_days=0.0,
        )
        enriched_explicit = enrich_event(explicit_event)
        self.assertEqual(enriched_explicit.attr_id, "builder")

    def test_aarav_aggregates(self):
        """Test 3: Compute Revealed Self aggregates over 21-day Aarav seed fixture."""
        seed_events = generate_aarav_seed_events()
        attr_ids = ["public_speaker", "builder"]

        revealed = build_revealed_aggregates(seed_events, attribute_ids=attr_ids, window_days=21)

        self.assertGreaterEqual(revealed.total_events, 25)
        self.assertIn("public_speaker", revealed.attribute_aggregates)
        self.assertIn("builder", revealed.attribute_aggregates)
        
        # Aarav has high consumption/drift and low creation -> create_consume_ratio < 1.0
        self.assertLess(revealed.create_consume_ratio, 1.0)
        self.assertGreater(revealed.attribute_aggregates["builder"].event_count, 0)
        self.assertGreater(revealed.attribute_aggregates["public_speaker"].event_count, 0)

    def test_digital_twin_assembly(self):
        """Test 4: Assemble DigitalTwinReadModel combining Aarav DeclaredSelf v1 and seed events."""
        aarav_declared = get_aarav_declared_self()
        seed_events = generate_aarav_seed_events()

        twin = assemble_digital_twin(
            user_id="aarav_demo",
            declared_self=aarav_declared,
            events=seed_events,
            window_days=21,
            timestamp="2026-08-01T12:00:00Z",
        )

        self.assertEqual(twin.user_id, "aarav_demo")
        self.assertEqual(twin.declared_version, 1)
        self.assertIn("public_speaker", twin.revealed_aggregates.attribute_aggregates)
        
        # Aarav's gap should be high due to consume-heavy evidence
        self.assertGreater(twin.gap_result.gap_score, 40)
        self.assertEqual(twin.gap_result.alignment, 100 - twin.gap_result.gap_score)


if __name__ == "__main__":
    unittest.main()
