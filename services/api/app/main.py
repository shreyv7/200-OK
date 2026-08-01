"""FastAPI application entrypoint. Owner: Backend."""

from __future__ import annotations

from fastapi import FastAPI

from app.api.dashboard import router as dashboard_router
from app.api.evidence import router as evidence_router
from app.api.health import router as health_router
from app.api.identity import router as identity_router
from app.api.lattice import router as lattice_router
from app.core.config import get_settings
from app.services.identity.wiring import register as register_identity_wiring

app = FastAPI(title="Trellis API", version="0.1.0")

app.include_router(health_router, prefix="/api/v1")
app.include_router(health_router)  # unprefixed convenience for liveness probes
app.include_router(evidence_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")
app.include_router(identity_router, prefix="/api/v1")
app.include_router(lattice_router, prefix="/api/v1")

register_identity_wiring()

_settings = get_settings()
if _settings.env == "local":
    from app.api.simulator import router as simulator_router

    app.include_router(simulator_router, prefix="/api/v1")
