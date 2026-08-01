"""Unit tests for AIA Milestone M4 (LLM Bottleneck Diagnosis & Growth Decision Engine).

Validates LLM path with FakeLLMProvider, fallback to v0, low-confidence flagging,
growth decision curation triggers, capacity intensity tiers, and Gap Firewall constraint.
Runs natively via python -m unittest / pytest.
"""

from datetime import datetime, timezone
import unittest

from app.providers.llm.fake import FakeLLMProvider
from app.services.decision.packet import BottleneckCandidate
from app.services.identity.bottleneck_v0 import diagnose_bottleneck_v0
from app.services.identity.bottleneck_v1 import diagnose_bottleneck_v1
from app.services.identity.growth_decision import evaluate_growth_decision
from app.services.identity.recompute import recompute_user_gap
from tests.fixtures.aarav_seed import (
    generate_aarav_seed_events,
    get_aarav_declared_self,
)


class TestM4Bottleneck(unittest.TestCase):

    def test_diagnose_bottleneck_v1_llm_path(self):
        """Test 1: diagnose_bottleneck_v1 returns candidates using FakeLLMProvider."""
        ref_time = datetime.now(timezone.utc)
        aarav_declared = get_aarav_declared_self()
        seed_events = generate_aarav_seed_events(ref_time=ref_time)
        fake_llm = FakeLLMProvider()

        gap_res, _, packet = recompute_user_gap(
            user_id="aarav_demo",
            declared_self=aarav_declared,
            events=seed_events,
            prior_gap_score=None,
            ref_time=ref_time,
            llm_provider=fake_llm,
        )

        self.assertGreater(len(packet.bottleneck_candidates), 0)
        top = packet.bottleneck_candidates[0]
        self.assertIn(top.label, ["execution", "consistency", "communication", "focus", "confidence", "discipline"])
        self.assertGreater(top.confidence, 0.0)

    def test_bottleneck_v1_fallback_to_v0(self):
        """Test 2: When LLM fails or is None, fallback to v0 occurs gracefully."""
        ref_time = datetime.now(timezone.utc)
        aarav_declared = get_aarav_declared_self()
        seed_events = generate_aarav_seed_events(ref_time=ref_time)

        # llm_provider=None falls back to v0
        _, _, packet_v0 = recompute_user_gap(
            user_id="aarav_demo",
            declared_self=aarav_declared,
            events=seed_events,
            ref_time=ref_time,
            llm_provider=None,
        )

        self.assertGreater(len(packet_v0.bottleneck_candidates), 0)

    def test_low_confidence_flag_trigger(self):
        """Test 3: low_confidence_flag is True when top candidate confidence < 0.65."""
        gap_res, _, _ = recompute_user_gap("aarav_demo", get_aarav_declared_self(), [])

        low_conf_candidates = [BottleneckCandidate(label="focus", confidence=0.55)]
        decision = evaluate_growth_decision(gap_res, bottleneck_candidates=low_conf_candidates)

        self.assertTrue(decision.low_confidence_flag)

        high_conf_candidates = [BottleneckCandidate(label="focus", confidence=0.85)]
        decision_high = evaluate_growth_decision(gap_res, bottleneck_candidates=high_conf_candidates)

        self.assertFalse(decision_high.low_confidence_flag)

    def test_growth_decision_curation_trigger(self):
        """Test 4: evaluate_growth_decision sets should_recurate=True on gap delta or C:C ratio drop."""
        gap_res, _, _ = recompute_user_gap("aarav_demo", get_aarav_declared_self(), [])

        # Delta >= 5 triggers re-curation
        decision = evaluate_growth_decision(gap_res, prior_gap_score=gap_res.gap_score - 10)
        self.assertTrue(decision.should_recurate)
        self.assertIn("shifted", decision.reason)

    def test_gap_firewall_constraint(self):
        """Test 5: GapResult score is 100% identical regardless of llm_provider presence (Gap Firewall)."""
        ref_time = datetime.now(timezone.utc)
        aarav_declared = get_aarav_declared_self()
        seed_events = generate_aarav_seed_events(ref_time=ref_time)
        fake_llm = FakeLLMProvider()

        gap_with_llm, _, _ = recompute_user_gap(
            "aarav_demo", aarav_declared, seed_events, ref_time=ref_time, llm_provider=fake_llm
        )
        gap_no_llm, _, _ = recompute_user_gap(
            "aarav_demo", aarav_declared, seed_events, ref_time=ref_time, llm_provider=None
        )

        self.assertEqual(gap_with_llm.gap_score, gap_no_llm.gap_score)
        self.assertEqual(gap_with_llm.alignment, gap_no_llm.alignment)

    def test_curation_intensity_capacity_mapping(self):
        """Test 6: Capacity percentages map to 'full', 'light', and 'micro' intensity tiers."""
        gap_res, _, _ = recompute_user_gap("aarav_demo", get_aarav_declared_self(), [])

        self.assertEqual(evaluate_growth_decision(gap_res, capacity_pct=100).curation_intensity, "full")
        self.assertEqual(evaluate_growth_decision(gap_res, capacity_pct=50).curation_intensity, "light")
        self.assertEqual(evaluate_growth_decision(gap_res, capacity_pct=20).curation_intensity, "micro")


if __name__ == "__main__":
    unittest.main()
