from __future__ import annotations

from unittest.mock import MagicMock, patch


def test_evidence_invalidate_enqueues_tier2_refresh() -> None:
    row = MagicMock()
    row.user_id = "user-aarav"

    graph_result = {
        "stack_draft": {"invalidate": True},
        "decision_packet": {"invalidateStack": True},
        "visited": ["coordinator"],
    }

    with patch("app.services.identity.wiring.SessionLocal") as mock_session_local:
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        with patch("app.services.identity.wiring.orchestration.recompute_and_persist") as mock_recompute:
            with patch("app.services.identity.wiring.evidence_repository.to_schema") as mock_schema:
                with patch(
                    "app.services.identity.wiring.emit_evidence_created", return_value=graph_result
                ) as mock_emit:
                    with patch("app.services.identity.wiring.enqueue_tier2_stack_refresh") as mock_enqueue:
                        from app.services.identity.wiring import _on_evidence_created

                        mock_recompute.return_value = None
                        mock_schema.return_value = object()

                        _on_evidence_created(row)

                        mock_emit.assert_called_once()
                        mock_enqueue.assert_called_once_with("user-aarav")
                        mock_db.close.assert_called_once()


def test_evidence_no_invalidate_skips_tier2_refresh() -> None:
    row = MagicMock()
    row.user_id = "user-aarav"

    graph_result = {
        "stack_draft": {"invalidate": False},
        "decision_packet": {"invalidateStack": False},
        "visited": ["coordinator"],
    }

    with patch("app.services.identity.wiring.SessionLocal") as mock_session_local:
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        with patch("app.services.identity.wiring.orchestration.recompute_and_persist") as mock_recompute:
            with patch("app.services.identity.wiring.evidence_repository.to_schema") as mock_schema:
                with patch(
                    "app.services.identity.wiring.emit_evidence_created", return_value=graph_result
                ):
                    with patch("app.services.identity.wiring.enqueue_tier2_stack_refresh") as mock_enqueue:
                        from app.services.identity.wiring import _on_evidence_created

                        mock_recompute.return_value = None
                        mock_schema.return_value = object()

                        _on_evidence_created(row)

                        mock_enqueue.assert_not_called()
                        mock_db.close.assert_called_once()
