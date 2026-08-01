from __future__ import annotations

from app.services.decision.packet import build_decision_packet
from app.services.identity.scoring.gap import GapResult
from app.services.recommendation.decision_adapter import to_schema_decision_packet
from tests.fixtures.sample_data import sample_gap_snapshot, sample_identity_stack


def test_to_schema_decision_packet_maps_aia_fields() -> None:
    gap_result = GapResult(gap_score=68, alignment=32, per_attribute=[])
    aia_packet = build_decision_packet(
        user_id="user-aarav",
        gap_result=gap_result,
        prior_gap_score=62,
        create_consume_ratio=0.42,
        timestamp="2026-08-01T00:00:00Z",
    )

    schema_packet = to_schema_decision_packet(
        aia_packet,
        consistency=0.55,
        momentum=-2.0,
    )

    assert schema_packet.userId == "user-aarav"
    assert schema_packet.gapDelta == 6.0
    assert schema_packet.invalidateStack is True
    assert schema_packet.rankingFeatures["gapScore"] == 68.0
    assert schema_packet.rankingFeatures["consistency"] == 0.55


def test_from_gap_snapshot_preserves_backend_delta() -> None:
    from app.services.recommendation.decision_adapter import from_gap_snapshot

    snapshot = sample_gap_snapshot(gap_delta=3.0, gap_score=65)
    packet = from_gap_snapshot(snapshot, invalidate_stack=False)

    assert packet.gapDelta == 3.0
    assert packet.invalidateStack is False
    assert packet.rankingFeatures["createConsumeRatio"] == 0.42
