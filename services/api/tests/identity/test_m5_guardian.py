"""Unit tests for AIA Milestone M5 (Guardian Gate & Trust Ledger Budget Integration).

Validates Guardian reason codes, daily cap cancellation, spacing delay, high dismissal
intensity downgrade, low capacity downgrade, growth decision budget suppression, and completion event Gap movement.
Runs natively via python -m unittest / pytest.
"""

from datetime import datetime, timezone
import unittest

from app.schemas.evidence import EvidenceEvent
from app.services.identity.growth_decision import evaluate_growth_decision
from app.services.identity.guardian_decision import evaluate_guardian_action
from app.services.identity.recompute import recompute_user_gap
from tests.fixtures.aarav_seed import (
    generate_aarav_seed_events,
    get_aarav_declared_self,
)


class TestM5Guardian(unittest.TestCase):

    def test_guardian_daily_cap_cancel(self):
        """Test 1: interventions_today >= 5 results in cancel action and daily_cap_reached reason."""
        decision = evaluate_guardian_action(
            capacity_pct=100,
            interventions_today=5,
            dismissal_rate=0.0,
            hours_since_last_intervention=4.0,
        )
        self.assertEqual(decision.action, "cancel")
        self.assertEqual(decision.reason_code, "daily_cap_reached")
        self.assertIn("5 growth touchpoints", decision.plain_language_reason)

    def test_guardian_too_frequent_delay(self):
        """Test 2: hours_since_last < 1.0 results in delay action and too_frequent reason."""
        decision = evaluate_guardian_action(
            capacity_pct=100,
            interventions_today=2,
            dismissal_rate=0.0,
            hours_since_last_intervention=0.5,
        )
        self.assertEqual(decision.action, "delay")
        self.assertEqual(decision.reason_code, "too_frequent")
        self.assertIn("recent", decision.plain_language_reason)

    def test_guardian_high_dismissal_downgrade(self):
        """Test 3: dismissal_rate >= 0.6 results in downgrade action and step-down intensity."""
        decision = evaluate_guardian_action(
            capacity_pct=100,
            interventions_today=1,
            dismissal_rate=0.7,
            hours_since_last_intervention=3.0,
            current_intensity="full",
        )
        self.assertEqual(decision.action, "downgrade")
        self.assertEqual(decision.intensity, "light")
        self.assertEqual(decision.reason_code, "high_dismissal_rate")

    def test_guardian_low_capacity_downgrade(self):
        """Test 4: capacity_pct < 34 results in downgrade action to micro intensity."""
        decision = evaluate_guardian_action(
            capacity_pct=20,
            interventions_today=1,
            dismissal_rate=0.0,
            hours_since_last_intervention=3.0,
            current_intensity="full",
        )
        self.assertEqual(decision.action, "downgrade")
        self.assertEqual(decision.intensity, "micro")
        self.assertEqual(decision.reason_code, "low_capacity")

    def test_guardian_allow_path(self):
        """Test 5: Normal conditions result in allow action and ok reason."""
        decision = evaluate_guardian_action(
            capacity_pct=80,
            interventions_today=2,
            dismissal_rate=0.1,
            hours_since_last_intervention=2.5,
            current_intensity="full",
        )
        self.assertEqual(decision.action, "allow")
        self.assertEqual(decision.reason_code, "ok")
        self.assertEqual(decision.intensity, "full")

    def test_growth_decision_budget_exhausted(self):
        """Test 6: evaluate_growth_decision returns should_recurate=False when interventions_today >= 5."""
        gap_res, _, _ = recompute_user_gap("aarav_demo", get_aarav_declared_self(), [])
        growth_decision = evaluate_growth_decision(gap_res, interventions_today=5)

        self.assertFalse(growth_decision.should_recurate)
        self.assertIn("exhausted", growth_decision.reason)

    def test_growth_decision_dismissal_downgrade(self):
        """Test 7: evaluate_growth_decision downgrades full intensity to light when dismissal_rate >= 0.6."""
        gap_res, _, _ = recompute_user_gap("aarav_demo", get_aarav_declared_self(), [])
        growth_decision = evaluate_growth_decision(gap_res, capacity_pct=100, dismissal_rate=0.75)

        self.assertEqual(growth_decision.curation_intensity, "light")

    def test_completion_event_lowers_gap(self):
        """Test 8: Completing a mission evidence event lowers the Identity Gap score for Aarav seed."""
        ref_time = datetime.now(timezone.utc)
        aarav_declared = get_aarav_declared_self()
        base_events = generate_aarav_seed_events(ref_time=ref_time)

        gap_before, _, _ = recompute_user_gap("aarav_demo", aarav_declared, base_events, ref_time=ref_time)

        # Add mission completion event
        completion_evt = EvidenceEvent(
            id="evt_test_completion",
            userId="aarav_demo",
            timestamp=ref_time.isoformat(),
            source="trellis",
            type="mission_completed",
            category="creation",
            identityAttributeIds=["public_speaker", "builder"],
            value=3.0,
            baseWeight=3.0,
            metadata={},
            simulated=True,
        )

        events_with_completion = base_events + [completion_evt]
        gap_after, _, _ = recompute_user_gap("aarav_demo", aarav_declared, events_with_completion, ref_time=ref_time)

        self.assertLess(gap_after.gap_score, gap_before.gap_score)


if __name__ == "__main__":
    unittest.main()
