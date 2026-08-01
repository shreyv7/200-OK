"""Unit tests for AIA Milestone M3 (Mirror Interview / Identity Agent).

Validates turn policy, weight auto-repair, unconfirmed safety, confirmation payload assembly,
and IdentityAgentNode extraction flow. Runs natively via python -m unittest / pytest.
"""

import unittest

from app.providers.llm.fake import FakeLLMProvider
from app.agents.nodes.identity.node import IdentityAgentNode
from app.services.identity.confirmation import (
    InterviewState,
    build_confirmation_payload,
)
from app.services.identity.extractor import validate_and_repair_extraction
from tests.fixtures.interview_transcript_seed import get_sample_aarav_transcript


class TestM3InterviewAgent(unittest.TestCase):

    def test_interview_turn_policy(self):
        """Test 1: Turn policy generates valid non-empty questions for turns 1 through 5."""
        node = IdentityAgentNode()
        state = InterviewState(userId="aarav_demo")

        for turn_idx in range(1, 6):
            state.currentTurn = turn_idx
            q = node.generate_next_interview_question(state)
            self.assertIsNotNone(q)
            self.assertGreater(len(q), 10)

    def test_extraction_weight_repair(self):
        """Test 2: validate_and_repair_extraction normalizes weights so sum(w_i) == 1.0."""
        raw_invalid_weights = {
            "version": 1,
            "attributes": [
                {"id": "a1", "label": "Attr 1", "weight": 0.6, "targetWeeklyPoints": 15.0},
                {"id": "a2", "label": "Attr 2", "weight": 0.6, "targetWeeklyPoints": 15.0},
            ],
        }

        is_valid, repaired, err = validate_and_repair_extraction(raw_invalid_weights, "aarav_demo")
        self.assertTrue(is_valid)
        self.assertIsNotNone(repaired)
        self.assertIsNone(err)

        total_weight = sum(attr.weight for attr in repaired.attributes)
        self.assertAlmostEqual(total_weight, 1.0, places=3)

    def test_unconfirmed_safety(self):
        """Test 3: Extracted DeclaredSelf has confirmedAt = None so active Twin is never overwritten prematurely."""
        raw_extraction = {
            "version": 1,
            "attributes": [
                {"id": "public_speaker", "label": "Public Speaker", "weight": 0.5, "targetWeeklyPoints": 15.0},
                {"id": "builder", "label": "Builder", "weight": 0.5, "targetWeeklyPoints": 15.0},
            ],
        }

        is_valid, repaired, err = validate_and_repair_extraction(raw_extraction, "aarav_demo")
        self.assertTrue(is_valid)
        self.assertIsNone(repaired.confirmedAt)

    def test_confirmation_payload_assembly(self):
        """Test 4: build_confirmation_payload builds summary narrative and attribute breakdown."""
        raw_extraction = {
            "version": 1,
            "attributes": [
                {"id": "public_speaker", "label": "Public Speaker", "weight": 0.5, "targetWeeklyPoints": 15.0},
                {"id": "builder", "label": "Builder", "weight": 0.5, "targetWeeklyPoints": 15.0},
            ],
        }

        _, declared_self, _ = validate_and_repair_extraction(raw_extraction, "aarav_demo")
        payload = build_confirmation_payload("aarav_demo", declared_self)

        self.assertEqual(payload.userId, "aarav_demo")
        self.assertTrue(payload.weightSumValid)
        self.assertIn("Did I get you right?", payload.promptMessage)
        self.assertEqual(len(payload.attributeBreakdown), 2)

    def test_identity_agent_extraction_flow(self):
        """Test 5: IdentityAgentNode extracts DeclaredSelf and ConfirmationPayload from transcript."""
        node = IdentityAgentNode()
        state = get_sample_aarav_transcript()
        fake_llm = FakeLLMProvider()

        is_valid, declared_self, payload = node.extract_declared_self(state, llm_provider=fake_llm)

        self.assertTrue(is_valid)
        self.assertIsNotNone(declared_self)
        self.assertIsNotNone(payload)
        self.assertEqual(declared_self.userId, "aarav_demo")
        self.assertEqual(payload.userId, "aarav_demo")


if __name__ == "__main__":
    unittest.main()
