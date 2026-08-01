"""Unit tests for AIA Milestone M7 (Weekly Report & Identity Evolution Agent).

Validates weekly report generation (v0 fallback and LLM-driven), identity evolution proposal
generation, citation validation (>= 3 evidence IDs required), and DeclaredSelf immutability.
Runs natively via python -m unittest / pytest.
"""

from datetime import datetime, timezone
import unittest

from app.services.identity.evolution_agent import propose_identity_evolution
from app.services.identity.recompute import recompute_user_gap
from app.services.identity.weekly_report import generate_weekly_report
from tests.fixtures.aarav_seed import (
    generate_aarav_seed_events,
    get_aarav_declared_self,
)


class FakeReportLLMProvider:
    """Fake LLM provider returning structured WeeklyReport output."""

    def generate_structured(self, schema: dict, messages: list) -> dict:
        return {
            "narrative": "Transformed public speaking fear into proactive community engagement across 2 major events.",
            "highlights": [
                "Attended 2 public speaking experiences in Pune",
                "Initiated 5 conversations, boosting confidence marker +9",
            ],
        }


class FakeEvolutionLLMProvider:
    """Fake LLM provider returning structured IdentityEvolutionProposal output."""

    def generate_structured(self, schema: dict, messages: list) -> dict:
        return {
            "narrative": "Behavioral evidence demonstrates strong emerging focus on entrepreneurship.",
            "proposedChanges": [
                {
                    "action": "add",
                    "attributeId": "entrepreneurship",
                    "attributeLabel": "Entrepreneur",
                    "newWeight": 0.25,
                    "reason": "Initiated multiple project discussions and artifact publications.",
                    "evidenceIds": ["evt_aarav_001", "evt_aarav_002", "evt_aarav_003"],
                }
            ],
        }


class TestM7ReportAndEvolution(unittest.TestCase):

    def test_weekly_report_v0_fallback(self):
        """Test 1: generate_weekly_report without LLM returns valid WeeklyReport with template narrative."""
        ref_time = datetime.now(timezone.utc)
        aarav_declared = get_aarav_declared_self()
        events = generate_aarav_seed_events(ref_time=ref_time)
        gap_res, _, _ = recompute_user_gap("aarav_demo", aarav_declared, events, ref_time=ref_time)

        report = generate_weekly_report(
            user_id="aarav_demo",
            declared_self=aarav_declared,
            events=events,
            gap_result=gap_res,
            prior_gap_score=50,
            llm_provider=None,
            ref_time=ref_time,
        )

        self.assertIsNotNone(report)
        self.assertEqual(report.userId, "aarav_demo")
        self.assertEqual(report.gapScoreEnd, gap_res.gap_score)
        self.assertEqual(report.gapScoreStart, 50)
        self.assertTrue(len(report.narrative) > 0)
        self.assertTrue(len(report.highlights) > 0)
        self.assertTrue(report.simulated)

    def test_weekly_report_llm_driven(self):
        """Test 2: generate_weekly_report with fake LLM returns narrative and highlights from LLM."""
        ref_time = datetime.now(timezone.utc)
        aarav_declared = get_aarav_declared_self()
        events = generate_aarav_seed_events(ref_time=ref_time)
        gap_res, _, _ = recompute_user_gap("aarav_demo", aarav_declared, events, ref_time=ref_time)
        llm = FakeReportLLMProvider()

        report = generate_weekly_report(
            user_id="aarav_demo",
            declared_self=aarav_declared,
            events=events,
            gap_result=gap_res,
            prior_gap_score=50,
            llm_provider=llm,
            ref_time=ref_time,
        )

        self.assertIn("speaking fear", report.narrative)
        self.assertEqual(len(report.highlights), 2)
        self.assertTrue(report.simulated)

    def test_evolution_agent_no_llm_returns_none(self):
        """Test 3: propose_identity_evolution without LLM provider returns None."""
        ref_time = datetime.now(timezone.utc)
        aarav_declared = get_aarav_declared_self()
        events = generate_aarav_seed_events(ref_time=ref_time)
        gap_res, _, _ = recompute_user_gap("aarav_demo", aarav_declared, events, ref_time=ref_time)

        proposal = propose_identity_evolution(
            user_id="aarav_demo",
            declared_self=aarav_declared,
            events=events,
            gap_result=gap_res,
            llm_provider=None,
            ref_time=ref_time,
        )

        self.assertIsNone(proposal)

    def test_evolution_agent_llm_driven(self):
        """Test 4: propose_identity_evolution with fake LLM returns valid proposal with cited evidence."""
        ref_time = datetime.now(timezone.utc)
        aarav_declared = get_aarav_declared_self()
        events = generate_aarav_seed_events(ref_time=ref_time)
        gap_res, _, _ = recompute_user_gap("aarav_demo", aarav_declared, events, ref_time=ref_time)
        llm = FakeEvolutionLLMProvider()

        proposal = propose_identity_evolution(
            user_id="aarav_demo",
            declared_self=aarav_declared,
            events=events,
            gap_result=gap_res,
            llm_provider=llm,
            ref_time=ref_time,
        )

        self.assertIsNotNone(proposal)
        self.assertEqual(proposal.userId, "aarav_demo")
        self.assertEqual(proposal.declaredSelfVersion, aarav_declared.version)
        self.assertEqual(len(proposal.proposedChanges), 1)
        self.assertEqual(proposal.proposedChanges[0].action, "add")
        self.assertEqual(proposal.proposedChanges[0].attributeId, "entrepreneurship")
        self.assertGreaterEqual(len(proposal.proposedChanges[0].evidenceIds), 3)

    def test_evolution_proposal_no_declared_self_mutation(self):
        """Test 5: propose_identity_evolution does not mutate DeclaredSelf."""
        ref_time = datetime.now(timezone.utc)
        aarav_declared = get_aarav_declared_self()
        attr_count_before = len(aarav_declared.attributes)
        version_before = aarav_declared.version
        events = generate_aarav_seed_events(ref_time=ref_time)
        gap_res, _, _ = recompute_user_gap("aarav_demo", aarav_declared, events, ref_time=ref_time)
        llm = FakeEvolutionLLMProvider()

        _ = propose_identity_evolution(
            user_id="aarav_demo",
            declared_self=aarav_declared,
            events=events,
            gap_result=gap_res,
            llm_provider=llm,
            ref_time=ref_time,
        )

        self.assertEqual(len(aarav_declared.attributes), attr_count_before)
        self.assertEqual(aarav_declared.version, version_before)


if __name__ == "__main__":
    unittest.main()
