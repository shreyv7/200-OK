"""Unit tests for AIA Milestone M8 (Demo Hardening & P2 Leverage Features).

Validates leverage-moment calendar feature extraction, Outside Voice lens evaluation,
DecisionPacket leverage_features payload, and demo projector Gap score delta legibility.
Runs natively via python -m unittest / pytest.
"""

from datetime import datetime, timedelta, timezone
import unittest

from app.schemas.evidence import EvidenceEvent
from app.services.identity.leverage_features import extract_leverage_features
from app.services.identity.outside_voice import (
    ALLOWED_DOMAINS,
    evaluate_outside_voice_lens,
)
from app.services.identity.recompute import recompute_user_gap
from tests.fixtures.aarav_seed import (
    generate_aarav_seed_events,
    get_aarav_declared_self,
)


class TestM8Hardening(unittest.TestCase):

    def test_leverage_features_upcoming_event(self):
        """Test 1: Calendar event 3 days away produces LeverageFeatures with rehearsal prep type."""
        ref_time = datetime.now(timezone.utc)
        cal_events = [
            {
                "id": "cal_evt_001",
                "title": "College Presentation on AI Ethics",
                "start_time": (ref_time + timedelta(days=3.0)).isoformat(),
                "attribute_id": "public_speaker",
            }
        ]
        declared = get_aarav_declared_self()

        features = extract_leverage_features(cal_events, declared, ref_time)
        self.assertIsNotNone(features)
        self.assertTrue(features.has_upcoming_event)
        self.assertEqual(features.event_id, "cal_evt_001")
        self.assertEqual(features.days_until_event, 3.0)
        self.assertEqual(features.suggested_prep_type, "rehearsal")
        self.assertEqual(features.relevant_attribute_id, "public_speaker")

    def test_leverage_features_far_or_past_event(self):
        """Test 2: Calendar event > 7 days away or in the past returns None."""
        ref_time = datetime.now(timezone.utc)
        cal_events = [
            {
                "id": "cal_evt_far",
                "title": "Future Presentation",
                "start_time": (ref_time + timedelta(days=10.0)).isoformat(),
            },
            {
                "id": "cal_evt_past",
                "title": "Past Presentation",
                "start_time": (ref_time - timedelta(days=1.0)).isoformat(),
            },
        ]
        declared = get_aarav_declared_self()

        features = extract_leverage_features(cal_events, declared, ref_time)
        self.assertIsNone(features)

    def test_recompute_attaches_leverage_features(self):
        """Test 3: recompute_user_gap attaches leverage_features to DecisionPacket when calendar_events provided."""
        ref_time = datetime.now(timezone.utc)
        aarav_declared = get_aarav_declared_self()
        events = generate_aarav_seed_events(ref_time=ref_time)

        cal_events = [
            {
                "id": "cal_demo_01",
                "title": "Project Demo Launch",
                "start_time": (ref_time + timedelta(days=2.0)).isoformat(),
                "attribute_id": "builder",
            }
        ]

        _, _, packet = recompute_user_gap(
            "aarav_demo", aarav_declared, events, ref_time=ref_time, calendar_events=cal_events
        )

        self.assertIsNotNone(packet.leverage_features)
        self.assertEqual(packet.leverage_features.suggested_prep_type, "quick_review")
        self.assertEqual(packet.leverage_features.event_id, "cal_demo_01")

    def test_outside_voice_lens_high_alignment(self):
        """Test 4: evaluate_outside_voice_lens returns recommendation from ALLOWED_DOMAINS when alignment >= 70%."""
        ref_time = datetime.now(timezone.utc)
        aarav_declared = get_aarav_declared_self()
        
        # Inject strong evidence to boost alignment >= 70 (Gap <= 30)
        strong_events = [
            EvidenceEvent(
                id=f"evt_strong_{i}",
                userId="aarav_demo",
                timestamp=ref_time,
                source="trellis",
                type="published_artifact",
                category="creation",
                identityAttributeIds=["public_speaker", "builder"],
                value=5.0,
                baseWeight=5.0,
                simulated=True,
            )
            for i in range(10)
        ]

        gap_res, _, _ = recompute_user_gap("aarav_demo", aarav_declared, strong_events, ref_time=ref_time)
        self.assertGreaterEqual(gap_res.alignment, 70)

        rec = evaluate_outside_voice_lens(aarav_declared, gap_res)
        self.assertIsNotNone(rec)
        self.assertIn(rec.domain, ALLOWED_DOMAINS)
        self.assertNotIn(rec.domain, [a.id for a in aarav_declared.attributes])

    def test_outside_voice_lens_low_alignment(self):
        """Test 5: evaluate_outside_voice_lens returns None when alignment < 70%."""
        ref_time = datetime.now(timezone.utc)
        aarav_declared = get_aarav_declared_self()
        base_events = generate_aarav_seed_events(ref_time=ref_time)

        gap_res, _, _ = recompute_user_gap("aarav_demo", aarav_declared, base_events, ref_time=ref_time)
        
        if gap_res.alignment < 70:
            rec = evaluate_outside_voice_lens(aarav_declared, gap_res)
            self.assertIsNone(rec)

    def test_projector_legibility_gap_delta(self):
        """Test 6: Completing a mission evidence event yields a sharp, projector-legible Gap score reduction (>= 8 points)."""
        ref_time = datetime.now(timezone.utc)
        aarav_declared = get_aarav_declared_self()
        base_events = generate_aarav_seed_events(ref_time=ref_time)

        gap_before, _, _ = recompute_user_gap("aarav_demo", aarav_declared, base_events, ref_time=ref_time)

        # Inject 2 completion missions
        completion_events = [
            EvidenceEvent(
                id=f"evt_demo_comp_{i}",
                userId="aarav_demo",
                timestamp=ref_time,
                source="trellis",
                type="published_artifact",
                category="creation",
                identityAttributeIds=["public_speaker", "builder"],
                value=5.0,
                baseWeight=5.0,
                simulated=True,
            )
            for i in range(2)
        ]

        events_after = base_events + completion_events
        gap_after, _, _ = recompute_user_gap("aarav_demo", aarav_declared, events_after, ref_time=ref_time)

        delta = gap_before.gap_score - gap_after.gap_score
        self.assertGreaterEqual(delta, 8)


if __name__ == "__main__":
    unittest.main()
