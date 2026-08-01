"""Unit tests for AIA Milestone M2 (Deterministic Gap, KPIs, Dashboard API).

Validates lattice contributor query, Bottleneck v0 engine, KPI snapshot, and recompute_user_gap.
Runs natively via python -m unittest / pytest.
"""

from datetime import datetime, timedelta, timezone
import unittest

from app.schemas.evidence import EvidenceEvent
from app.services.identity.lattice import get_lattice_strut_detail
from app.services.identity.bottleneck_v0 import diagnose_bottleneck_v0
from app.services.identity.kpi import build_kpi_snapshot
from app.services.identity.recompute import recompute_user_gap
from tests.fixtures.aarav_seed import (
    get_aarav_declared_self,
    generate_aarav_seed_events,
)


class TestM2GapKPIs(unittest.TestCase):

    def test_lattice_strut_detail(self):
        """Test 1: Lattice strut contributor query returns decayed contributions sorted descending."""
        ref_time = datetime.now(timezone.utc)
        aarav_declared = get_aarav_declared_self()
        seed_events = generate_aarav_seed_events(ref_time=ref_time)
        public_speaker_attr = aarav_declared.attributes[0]

        detail = get_lattice_strut_detail(
            attr=public_speaker_attr,
            events=seed_events,
            window_days=21,
            ref_time=ref_time,
            limit=10,
        )

        self.assertEqual(detail.attrId, "public_speaker")
        self.assertEqual(detail.attrLabel, "Public Speaker")
        self.assertGreater(len(detail.contributingEvents), 0)

        # Check sorting: highest decayed contribution first
        for i in range(len(detail.contributingEvents) - 1):
            self.assertGreaterEqual(
                detail.contributingEvents[i].decayedContribution,
                detail.contributingEvents[i + 1].decayedContribution,
            )

    def test_bottleneck_v0_diagnosis(self):
        """Test 2: Heuristic Bottleneck v0 produces valid candidate for consume-heavy Aarav history."""
        ref_time = datetime.now(timezone.utc)
        aarav_declared = get_aarav_declared_self()
        seed_events = generate_aarav_seed_events(ref_time=ref_time)

        gap_res, kpi_snap, packet = recompute_user_gap(
            user_id="aarav_demo",
            declared_self=aarav_declared,
            events=seed_events,
            prior_gap_score=None,
            window_days=21,
            ref_time=ref_time,
        )

        self.assertGreater(len(packet.bottleneck_candidates), 0)
        top_candidate = packet.bottleneck_candidates[0]
        self.assertIn(top_candidate.label, ["execution", "consistency", "communication", "focus"])
        self.assertGreater(top_candidate.confidence, 0.5)

    def test_recompute_user_gap(self):
        """Test 3: recompute_user_gap returns consistent GapResult, KPISnapshot, and DecisionPacket."""
        ref_time = datetime.now(timezone.utc)
        aarav_declared = get_aarav_declared_self()
        seed_events = generate_aarav_seed_events(ref_time=ref_time)

        gap_res, kpi_snap, packet = recompute_user_gap(
            user_id="aarav_demo",
            declared_self=aarav_declared,
            events=seed_events,
            prior_gap_score=80,
            window_days=21,
            ref_time=ref_time,
        )

        self.assertEqual(packet.user_id, "aarav_demo")
        self.assertEqual(packet.gap_score, gap_res.gap_score)
        self.assertEqual(kpi_snap.gapScore, gap_res.gap_score)
        self.assertEqual(kpi_snap.alignment, 100 - gap_res.gap_score)
        self.assertEqual(packet.gap_delta, gap_res.gap_score - 80)
        self.assertTrue(packet.invalidate_stack)

    def test_creation_injection_lowers_gap(self):
        """Test 4: Injecting a mission_completed creation event lowers Gap score without LLM calls."""
        ref_time = datetime.now(timezone.utc)
        aarav_declared = get_aarav_declared_self()
        seed_events = generate_aarav_seed_events(ref_time=ref_time)

        gap_before, _, _ = recompute_user_gap("aarav_demo", aarav_declared, seed_events, ref_time=ref_time)

        # Inject high-value creation event
        new_event = EvidenceEvent(
            id="evt_new_creation",
            userId="aarav_demo",
            timestamp=ref_time,
            source="trellis",
            type="mission_completed",
            category="creation",
            identityAttributeIds=["public_speaker"],
            baseWeight=5.0,
            value=5.0,
            simulated=True,
        )
        updated_events = [new_event] + seed_events

        gap_after, _, packet_after = recompute_user_gap(
            "aarav_demo", aarav_declared, updated_events, prior_gap_score=gap_before.gap_score, ref_time=ref_time
        )

        self.assertLess(gap_after.gap_score, gap_before.gap_score)
        self.assertLess(packet_after.gap_delta, 0)

    def test_drift_injection_raises_gap(self):
        """Test 5: Injecting focus_drift_10min raises Gap score without LLM calls."""
        ref_time = datetime.now(timezone.utc)
        aarav_declared = get_aarav_declared_self()
        seed_events = generate_aarav_seed_events(ref_time=ref_time)

        gap_before, _, _ = recompute_user_gap("aarav_demo", aarav_declared, seed_events, ref_time=ref_time)

        # Inject 3 consecutive drift events
        drift_events = [
            EvidenceEvent(
                id=f"evt_drift_{i}",
                userId="aarav_demo",
                timestamp=ref_time,
                source="trellis",
                type="focus_drift_10min",
                category="focus_drift",
                identityAttributeIds=["builder"],
                baseWeight=-2.0,
                value=-2.0,
                simulated=True,
            )
            for i in range(3)
        ]
        updated_events = drift_events + seed_events

        gap_after, _, packet_after = recompute_user_gap(
            "aarav_demo", aarav_declared, updated_events, prior_gap_score=gap_before.gap_score, ref_time=ref_time
        )

        self.assertGreater(gap_after.gap_score, gap_before.gap_score)
        self.assertGreater(packet_after.gap_delta, 0)


if __name__ == "__main__":
    unittest.main()
