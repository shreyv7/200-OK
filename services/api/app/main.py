"""FastAPI application entrypoint. Owner: Backend."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.agents import router as agents_router
from app.api.calendar import router as calendar_router
from app.api.capacity import router as capacity_router
from app.api.catalog import router as catalog_router
from app.api.dashboard import router as dashboard_router
from app.api.evidence import router as evidence_router
from app.api.github import router as github_router
from app.api.health import router as health_router
from app.api.identity import router as identity_router
from app.api.integrations import router as integrations_router
from app.api.ledger import router as ledger_router
from app.api.lattice import router as lattice_router
from app.api.me import router as me_router
from app.api.onboarding import router as onboarding_router
from app.api.partners import router as partners_router
from app.api.stack import router as stack_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.telemetry import TraceContextMiddleware
from app.services.identity.wiring import register as register_identity_wiring

configure_logging()

app = FastAPI(title="Trellis API", version="0.1.0")

app.add_middleware(TraceContextMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api/v1")
app.include_router(health_router)  # unprefixed convenience for liveness probes
app.include_router(me_router, prefix="/api/v1")
app.include_router(evidence_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")
app.include_router(identity_router, prefix="/api/v1")
app.include_router(integrations_router, prefix="/api/v1")
app.include_router(github_router, prefix="/api/v1")


app.include_router(lattice_router, prefix="/api/v1")
app.include_router(onboarding_router, prefix="/api/v1")
app.include_router(stack_router, prefix="/api/v1")
app.include_router(capacity_router, prefix="/api/v1")
app.include_router(ledger_router, prefix="/api/v1")
app.include_router(catalog_router, prefix="/api/v1")
app.include_router(agents_router, prefix="/api/v1")
app.include_router(calendar_router, prefix="/api/v1")
app.include_router(partners_router, prefix="/api/v1")

register_identity_wiring()

_settings = get_settings()
if _settings.env == "local":
    from app.api.simulator import router as simulator_router

    app.include_router(simulator_router, prefix="/api/v1")
