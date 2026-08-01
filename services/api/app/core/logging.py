"""Structured JSON logging. Owner: Backend. milestones.md M8 (techstack.md §22).

LangSmith is explicitly optional (milestones.md M8) — not wired here;
this covers the "structured logs" half of the checkbox only.
"""

from __future__ import annotations

import json
import logging
import sys


from app.core.telemetry import (
    get_current_run_id,
    get_current_trace_id,
    get_current_user_id_context,
)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        trace_id = getattr(record, "trace_id", None) or get_current_trace_id()
        user_id = getattr(record, "user_id", None) or get_current_user_id_context()
        run_id = getattr(record, "run_id", None) or get_current_run_id()

        payload = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "trace_id": trace_id,
            "user_id": user_id,
            "run_id": run_id,
        }
        return json.dumps(payload)



def configure_logging(level: int = logging.INFO) -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)
