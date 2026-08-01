from __future__ import annotations

from app.services.recommendation.demo_dryrun import run_demo_dryrun


def test_full_loop_dry_run_covers_demo_beats_without_empty_states() -> None:
    trace = run_demo_dryrun(user_id="user-aarav")

    beat_names = {beat["beat"] for beat in trace.beats}
    assert "beat1_mirror" in beat_names
    assert "beat2_dismissal" in beat_names
    assert "beat3_protection" in beat_names
    assert "beat4_proof" in beat_names

    dismissals = [beat for beat in trace.beats if beat["beat"] == "beat2_dismissal"]
    assert len(dismissals) == 3
    assert dismissals[-1]["unlearning_triggered"] is True

    proof = next(beat for beat in trace.beats if beat["beat"] == "beat4_proof")
    assert proof["prepared_alternate_ready"] is True
    assert proof["completion_verdict"] == "worked"
