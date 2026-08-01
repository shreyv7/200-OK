"""FastAPI application entrypoint. Owner: Backend."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.agents import router as agents_router
from app.api.calendar import router as calendar_router
from app.api.capacity import router as capacity_router
from app.api.catalog import router as catalog_router
from app.api.dashboard import router as dashboard_router
from app.api.evidence import router as evidence_router
from app.api.feed import router as feed_router
from app.api.github import router as github_router
from app.api.health import router as health_router
from app.api.identity import router as identity_router
from app.api.integrations import router as integrations_router
from app.api.ledger import router as ledger_router
from app.api.lattice import router as lattice_router
from app.api.me import router as me_router
from app.api.notion import router as notion_router
from app.api.onboarding import router as onboarding_router
from app.api.partners import router as partners_router
from app.api.screentime import router as screentime_router
from app.api.search import router as search_router
from app.api.stack import router as stack_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.telemetry import TraceContextMiddleware
from app.providers.llm.budget import LLMBudgetExceeded
from app.services.identity.wiring import register as register_identity_wiring

configure_logging()

app = FastAPI(title="Trellis API", version="0.1.0")

_settings = get_settings()

app.add_middleware(TraceContextMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_settings.cors_origin_list or ["http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(LLMBudgetExceeded)
async def _llm_budget_exceeded_handler(_request: Request, exc: LLMBudgetExceeded) -> JSONResponse:
    """B5 (docs/work.md): one place all routers get this for free instead
    of each needing its own try/except around an LLM-calling service."""
    return JSONResponse(
        status_code=429,
        content={"error_code": "llm_budget_exceeded", "detail": str(exc)},
    )


app.include_router(health_router, prefix="/api/v1")
app.include_router(health_router)  # unprefixed convenience for liveness probes
app.include_router(me_router, prefix="/api/v1")
app.include_router(evidence_router, prefix="/api/v1")
app.include_router(feed_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")
app.include_router(identity_router, prefix="/api/v1")
app.include_router(integrations_router, prefix="/api/v1")
app.include_router(github_router, prefix="/api/v1")
app.include_router(notion_router, prefix="/api/v1")


app.include_router(lattice_router, prefix="/api/v1")
app.include_router(onboarding_router, prefix="/api/v1")
app.include_router(stack_router, prefix="/api/v1")
app.include_router(capacity_router, prefix="/api/v1")
app.include_router(ledger_router, prefix="/api/v1")
app.include_router(catalog_router, prefix="/api/v1")
app.include_router(agents_router, prefix="/api/v1")
app.include_router(calendar_router, prefix="/api/v1")
app.include_router(partners_router, prefix="/api/v1")
app.include_router(search_router, prefix="/api/v1")
app.include_router(screentime_router, prefix="/api/v1")

register_identity_wiring()

if _settings.env == "local":
    from app.api.simulator import router as simulator_router

    app.include_router(simulator_router, prefix="/api/v1")
