"""Unit tests for AIA Milestone M1 (Evidence Pipeline + Twin Shell).

Validates event sanitizer, rule-based enrichment, Revealed Self aggregates, and Digital Twin assembly
using Backend Pydantic models (app.schemas.evidence & app.schemas.identity).
"""

from datetime import datetime, timezone
import unittest

from app.schemas.evidence import EvidenceEvent
from app.services.identity.sanitizer import validate_and_sanitize_event, get_event_delta_days
from app.services.identity.enrichment import enrich_evidence_event
from app.services.identity.aggregates import build_revealed_aggregates
from app.services.identity.twin import assemble_digital_twin
from tests.fixtures.aarav_seed import (
    get_aarav_declared_self,
    generate_aarav_seed_events,
)


class TestM1EvidencePipeline(unittest.TestCase):

    def test_sanitizer_validation(self):
        """Test 1: Sanitizer accepts valid events and rejects corrupt/out-of-bounds payloads."""
        valid_raw = {
            "userId": "user_123",
            "type": "github_commit",
            "category": "creation",
            "source": "github",
            "baseWeight": 4.0,
            "value": 4.0,
            "simulated": True,
        }
        is_valid, evt, err = validate_and_sanitize_event(valid_raw)
        self.assertTrue(is_valid)
        self.assertIsNotNone(evt)
        self.assertIsNone(err)
        self.assertEqual(evt.userId, "user_123")
        self.assertEqual(evt.type, "github_commit")

        # Invalid: missing userId
        is_valid, evt, err = validate_and_sanitize_event({"type": "github_commit"})
        self.assertFalse(is_valid)
        self.assertIn("userId", err)

        # Invalid: missing type
        is_valid, evt, err = validate_and_sanitize_event({"userId": "user_123"})
        self.assertFalse(is_valid)
        self.assertIn("type", err)

    def test_enrichment_mapping(self):
        """Test 2: Rule-based enrichment maps keyword content to identityAttributeIds."""
        unmapped_event = EvidenceEvent(
            id="e1",
            userId="aarav_demo",
            timestamp=datetime.now(timezone.utc),
            source="trellis",
            type="passive_item",
            category="passive_learning",
            identityAttributeIds=[],
            value=1.0,
            baseWeight=1.0,
            metadata={"title": "Watched 20min speech analysis video"},
        )

        enriched = enrich_evidence_event(unmapped_event)
        self.assertIn("public_speaker", enriched.identityAttributeIds)

        # Explicit identityAttributeIds should be preserved
        explicit_event = EvidenceEvent(
            id="e2",
            userId="aarav_demo",
            timestamp=datetime.now(timezone.utc),
            source="github",
            type="github_commit",
            category="creation",
            identityAttributeIds=["builder"],
            value=4.0,
            baseWeight=4.0,
        )
        enriched_explicit = enrich_evidence_event(explicit_event)
        self.assertEqual(enriched_explicit.identityAttributeIds, ["builder"])

    def test_aarav_aggregates(self):
        """Test 3: Compute Revealed Self aggregates over 21-day Aarav seed fixture."""
        ref_time = datetime.now(timezone.utc)
        seed_events = generate_aarav_seed_events(ref_time=ref_time)
        attr_ids = ["public_speaker", "builder"]

        revealed = build_revealed_aggregates(seed_events, attribute_ids=attr_ids, window_days=21, ref_time=ref_time)

        self.assertGreaterEqual(revealed.total_events, 25)
        self.assertIn("public_speaker", revealed.attribute_aggregates)
        self.assertIn("builder", revealed.attribute_aggregates)
        
        # Aarav has high consumption/drift and low creation -> create_consume_ratio < 1.0
        self.assertLess(revealed.create_consume_ratio, 1.0)
        self.assertGreater(revealed.attribute_aggregates["builder"].event_count, 0)
        self.assertGreater(revealed.attribute_aggregates["public_speaker"].event_count, 0)

    def test_digital_twin_assembly(self):
        """Test 4: Assemble DigitalTwinReadModel combining Aarav DeclaredSelf Pydantic model and seed events."""
        ref_time = datetime.now(timezone.utc)
        aarav_declared = get_aarav_declared_self()
        seed_events = generate_aarav_seed_events(ref_time=ref_time)

        twin = assemble_digital_twin(
            user_id="aarav_demo",
            declared_self=aarav_declared,
            events=seed_events,
            window_days=21,
            ref_time=ref_time,
        )

        self.assertEqual(twin.userId, "aarav_demo")
        self.assertEqual(twin.declaredVersion, 1)
        self.assertIn("public_speaker", twin.revealedAggregates.attribute_aggregates)
        
        # Aarav's gap should be high due to consume-heavy evidence
        self.assertGreater(twin.gapResult.gap_score, 40)
        self.assertEqual(twin.gapResult.alignment, 100 - twin.gapResult.gap_score)


if __name__ == "__main__":
    unittest.main()
