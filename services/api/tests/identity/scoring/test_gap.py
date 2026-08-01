"""Unit tests for AIA Gap formula edge cases and constants (M0).

Validates PRD §9 deterministic scoring behavior without database or LLM dependencies.
Runs natively via python -m unittest.
"""

import math
import unittest

from app.services.identity.scoring.constants import (
    LAMBDA,
    EVENT_WEIGHTS,
    DEFAULT_DECLARED_TARGET,
    GAP_DELTA_INVALIDATION_THRESHOLD,
)
from app.services.identity.scoring.declared_self import (
    IdentityAttribute,
    validate_weights,
    get_declared_self_json_schema,
)
from app.services.identity.scoring.gap import (
    EvidenceInput,
    AttrInput,
    decay_weight,
    compute_deficit,
    compute_gap_score,
    compute_create_consume,
    compute_consistency,
    compute_momentum,
)
from app.services.decision.packet import (
    build_decision_packet,
    BOTTLENECK_TAXONOMY,
)


class TestGapFormula(unittest.TestCase):

    def test_decay_weight_half_life(self):
        """Fixture D — Decay test: 7-day old event has a decay factor of exactly 0.5."""
        decay_0 = decay_weight(0.0)
        decay_7 = decay_weight(7.0)
        self.assertTrue(math.isclose(decay_0, 1.0, abs_tol=1e-6))
        self.assertTrue(math.isclose(decay_7, 0.5, abs_tol=1e-4))

    def test_compute_deficit_clamping(self):
        """Fixture E — Clamp test: deficit is bounded in [0.0, 1.0]."""
        # Overachievement (R_i > D_i) -> deficit should clamp to 0.0
        self.assertEqual(compute_deficit(D_i=10.0, R_i=15.0), 0.0)
        # Complete absence (R_i = 0) -> deficit should be 1.0
        self.assertEqual(compute_deficit(D_i=10.0, R_i=0.0), 1.0)
        # Partial achievement -> (10 - 5) / 10 = 0.5
        self.assertEqual(compute_deficit(D_i=10.0, R_i=5.0), 0.5)
        # Non-positive declared target -> 0.0
        self.assertEqual(compute_deficit(D_i=0.0, R_i=5.0), 0.0)

    def test_fully_aligned_persona(self):
        """Fixture A — Fully aligned persona: R_i >= D_i yields Gap = 0, Alignment = 100."""
        attrs = [
            AttrInput(attr_id="public_speaker", w_i=0.6, D_i=10.0),
            AttrInput(attr_id="builder", w_i=0.4, D_i=10.0),
        ]
        # Provide events satisfying both targets
        events = [
            EvidenceInput(event_type="published_artifact", attr_id="public_speaker", a_ik=1.0, delta_days=0.0),  # +5.0
            EvidenceInput(event_type="published_artifact", attr_id="public_speaker", a_ik=1.0, delta_days=0.0),  # +5.0 -> total 10.0
            EvidenceInput(event_type="github_commit", attr_id="builder", a_ik=1.0, delta_days=0.0),              # +4.0
            EvidenceInput(event_type="github_commit", attr_id="builder", a_ik=1.0, delta_days=0.0),              # +4.0
            EvidenceInput(event_type="mission_completed", attr_id="builder", a_ik=1.0, delta_days=0.0),          # +3.0 -> total 11.0
        ]

        res = compute_gap_score(attrs, events)
        self.assertEqual(res.gap_score, 0)
        self.assertEqual(res.alignment, 100)
        self.assertEqual(len(res.per_attribute), 2)
        self.assertEqual(res.per_attribute[0].deficit, 0.0)
        self.assertEqual(res.per_attribute[1].deficit, 0.0)

    def test_fully_drifted_persona(self):
        """Fixture B — Fully drifted persona: zero positive events yields Gap = 100, Alignment = 0."""
        attrs = [
            AttrInput(attr_id="public_speaker", w_i=0.5, D_i=15.0),
            AttrInput(attr_id="builder", w_i=0.5, D_i=15.0),
        ]
        events = []  # No evidence

        res = compute_gap_score(attrs, events)
        self.assertEqual(res.gap_score, 100)
        self.assertEqual(res.alignment, 0)

    def test_aarav_partial_drift(self):
        """Fixture C — Partial drift (Aarav-like): high passive consumption, low creation."""
        attrs = [
            AttrInput(attr_id="public_speaker", w_i=0.5, D_i=15.0),
            AttrInput(attr_id="builder", w_i=0.5, D_i=15.0),
        ]
        events = [
            # Watched tutorials (passive)
            EvidenceInput(event_type="passive_item", attr_id="public_speaker", a_ik=1.0, delta_days=1.0),  # ~0.9
            EvidenceInput(event_type="passive_item", attr_id="builder", a_ik=1.0, delta_days=2.0),         # ~0.8
            # Focus drift
            EvidenceInput(event_type="focus_drift_10min", attr_id="builder", a_ik=1.0, delta_days=0.0),   # -2.0
        ]

        res = compute_gap_score(attrs, events)
        self.assertTrue(40 < res.gap_score < 100)
        self.assertEqual(res.alignment, 100 - res.gap_score)

        # Create:Consume ratio check
        cc_res = compute_create_consume(events)
        self.assertEqual(cc_res.create_points, 0.0)
        self.assertLess(cc_res.ratio, 1.0)

    def test_creation_event_lowers_gap(self):
        """Fixture F — Creation event lowers gap score."""
        attrs = [AttrInput(attr_id="builder", w_i=1.0, D_i=10.0)]
        initial_events = [EvidenceInput(event_type="passive_item", attr_id="builder", a_ik=1.0, delta_days=0.0)]

        before = compute_gap_score(attrs, initial_events)

        # Add a high-value creation event
        after_events = initial_events + [
            EvidenceInput(event_type="published_artifact", attr_id="builder", a_ik=1.0, delta_days=0.0)  # +5.0
        ]
        after = compute_gap_score(attrs, after_events)

        self.assertLess(after.gap_score, before.gap_score)

    def test_drift_event_raises_gap(self):
        """Fixture G — Focus drift event reduces R_i and raises deficit."""
        attrs = [AttrInput(attr_id="builder", w_i=1.0, D_i=10.0)]
        initial_events = [EvidenceInput(event_type="github_commit", attr_id="builder", a_ik=1.0, delta_days=0.0)]  # +4.0

        before = compute_gap_score(attrs, initial_events)

        # Add focus drift
        after_events = initial_events + [
            EvidenceInput(event_type="focus_drift_10min", attr_id="builder", a_ik=1.0, delta_days=0.0)  # -2.0
        ]
        after = compute_gap_score(attrs, after_events)

        self.assertGreater(after.gap_score, before.gap_score)

    def test_validate_weights(self):
        """Fixture H — Weight sum validation."""
        valid_attrs: list[IdentityAttribute] = [
            {"id": "a1", "label": "A1", "description": "", "weight": 0.7, "markers": [], "declared_weekly_target": 10.0},
            {"id": "a2", "label": "A2", "description": "", "weight": 0.3, "markers": [], "declared_weekly_target": 10.0},
        ]
        invalid_attrs: list[IdentityAttribute] = [
            {"id": "a1", "label": "A1", "description": "", "weight": 0.7, "markers": [], "declared_weekly_target": 10.0},
            {"id": "a2", "label": "A2", "description": "", "weight": 0.5, "markers": [], "declared_weekly_target": 10.0},
        ]

        self.assertTrue(validate_weights(valid_attrs))
        self.assertFalse(validate_weights(invalid_attrs))
        self.assertFalse(validate_weights([]))

    def test_decision_packet_construction(self):
        """Fixture I — DecisionPacket construction and invalidation flag trigger."""
        attrs = [AttrInput(attr_id="builder", w_i=1.0, D_i=10.0)]
        events = [EvidenceInput(event_type="github_commit", attr_id="builder", a_ik=1.0, delta_days=0.0)]
        gap_res = compute_gap_score(attrs, events)

        # Prior gap = 80, current gap = 60 -> delta = -20 -> abs(delta) >= 5 -> invalidate_stack = True
        packet = build_decision_packet(
            user_id="aarav_demo",
            gap_result=gap_res,
            prior_gap_score=80,
            create_consume_ratio=1.5,
            timestamp="2026-08-01T12:00:00Z",
        )

        self.assertEqual(packet.user_id, "aarav_demo")
        self.assertEqual(packet.gap_score, gap_res.gap_score)
        self.assertEqual(packet.gap_delta, gap_res.gap_score - 80)
        self.assertTrue(packet.invalidate_stack)
        self.assertIn("confidence", BOTTLENECK_TAXONOMY)

    def test_declared_self_schema(self):
        """Verify JSON schema generation for DeclaredSelf target."""
        schema = get_declared_self_json_schema()
        self.assertEqual(schema["title"], "DeclaredSelf")
        self.assertIn("attributes", schema["properties"])


if __name__ == "__main__":
    unittest.main()
