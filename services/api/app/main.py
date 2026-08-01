"""FastAPI application entrypoint. Owner: Backend."""

from __future__ import annotations

from fastapi import FastAPI

from app.api.health import router as health_router

app = FastAPI(title="Trellis API", version="0.1.0")

app.include_router(health_router, prefix="/api/v1")
app.include_router(health_router)  # unprefixed convenience for liveness probes
