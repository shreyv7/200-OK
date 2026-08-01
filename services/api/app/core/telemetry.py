"""Telemetry and Context Propagation module. Owner: Backend (Task C6).

Propagates trace_id, user_id, and run_id context variables across incoming HTTP
requests, background Celery tasks, and structured logging.
"""

from __future__ import annotations

import uuid
from contextvars import ContextVar
from typing import Callable, Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

trace_id_var: ContextVar[Optional[str]] = ContextVar("trace_id", default=None)
user_id_var: ContextVar[Optional[str]] = ContextVar("user_id", default=None)
run_id_var: ContextVar[Optional[str]] = ContextVar("run_id", default=None)


def get_current_trace_id() -> str | None:
    return trace_id_var.get()


def get_current_user_id_context() -> str | None:
    return user_id_var.get()


def get_current_run_id() -> str | None:
    return run_id_var.get()


def set_telemetry_context(
    trace_id: str | None = None,
    user_id: str | None = None,
    run_id: str | None = None,
) -> None:
    if trace_id is not None:
        trace_id_var.set(trace_id)
    if user_id is not None:
        user_id_var.set(user_id)
    if run_id is not None:
        run_id_var.set(run_id)


class TraceContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        trace_id = request.headers.get("X-Trace-ID") or f"tr-{uuid.uuid4().hex[:12]}"
        user_id = request.headers.get("X-User-ID") or request.headers.get("Authorization") or None
        run_id = request.headers.get("X-Run-ID") or f"run-{uuid.uuid4().hex[:8]}"

        trace_id_var.set(trace_id)
        user_id_var.set(user_id)
        run_id_var.set(run_id)

        response = await call_next(request)
        response.headers["X-Trace-ID"] = trace_id
        response.headers["X-Run-ID"] = run_id
        return response
