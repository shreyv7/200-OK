"""Dev-only simulator inject endpoint. Owner: Backend. F2 (prd.md), milestones.md M1.

Mounted only when settings.env == "local" (see main.py). Injects events
through the same FixtureTrellisAdapter + evidence_service path used by
real ingest — never a raw/pre-scored insert (guidelines.md §9.2).
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.di import get_current_user_id, get_db
from app.integrations.mcp.trellis.adapter import FixtureTrellisAdapter
from app.schemas.evidence import EvidenceEvent, RawMCPPayload
from app.services.evidence import service as evidence_service

router = APIRouter(tags=["simulator"])

_adapter = FixtureTrellisAdapter()


class SimulatorInjectRequest(BaseModel):
    scenario: Literal["doomscroll_burst", "time_advance"]
    params: dict = {}


@router.post("/simulator/inject", response_model=list[EvidenceEvent])
def inject(
    request: SimulatorInjectRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
) -> list[EvidenceEvent]:
    now = datetime.utcnow()
    created: list[EvidenceEvent] = []

    if request.scenario == "doomscroll_burst":
        minutes = request.params.get("minutes", 20)
        chunks = max(1, int(minutes // 10))
        for i in range(chunks):
            event_timestamp = now - timedelta(minutes=10 * (chunks - i))
            raw = RawMCPPayload(
                sourceProvider="trellis",
                rawPayload={
                    "userId": user_id,
                    "type": "focus_drift_10min",
                    "timestamp": event_timestamp.isoformat(),
                    "units": 1.0,
                    "metadata": {"scenario": "doomscroll_burst", "chunk": i},
                },
            )
            event = _adapter.normalize(raw)
            ingest_request = evidence_service.request_from_event(event)
            _row, is_new = evidence_service.ingest(db, ingest_request)
            if is_new:
                created.append(event)

    elif request.scenario == "time_advance":
        days = request.params.get("days", 1)
        raw = RawMCPPayload(
            sourceProvider="trellis",
            rawPayload={
                "userId": user_id,
                "type": "passive_item",
                "timestamp": (now - timedelta(days=days)).isoformat(),
                "units": 1.0,
                "metadata": {"scenario": "time_advance", "days": days},
            },
        )
        event = _adapter.normalize(raw)
        ingest_request = evidence_service.request_from_event(event)
        _row, is_new = evidence_service.ingest(db, ingest_request)
        if is_new:
            created.append(event)

    return created
