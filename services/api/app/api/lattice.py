"""Lattice strut contributor endpoint. Owner: Backend. F3 (prd.md), milestones.md M2."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.di import get_current_user_id, get_db
from app.repositories import evidence_repository, twin_repository
from app.schemas.lattice import LatticeContributor, LatticeStrutResponse
from app.services.identity.enrichment import enrich_evidence_event
from app.services.identity.lattice import get_lattice_strut_detail
from app.services.identity.orchestration import WINDOW_DAYS

router = APIRouter(tags=["lattice"])


@router.get(
    "/identity/attributes/{attr_id}/evidence",
    response_model=LatticeStrutResponse,
)
def get_lattice_strut(
    attr_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
) -> LatticeStrutResponse:
    declared_self = twin_repository.get_active_declared_self(db, user_id)
    if declared_self is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No confirmed identity yet — complete onboarding first.",
        )

    attr = next((a for a in declared_self.attributes if a.id == attr_id), None)
    if attr is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown identity attribute: {attr_id}",
        )

    rows = evidence_repository.list_window(db, user_id, limit=1000)
    events = [evidence_repository.to_schema(row) for row in rows]
    events = [enrich_evidence_event(e, declared_self) for e in events]

    detail = get_lattice_strut_detail(attr, events, window_days=WINDOW_DAYS)

    return LatticeStrutResponse(
        attrId=detail.attrId,
        attrLabel=detail.attrLabel,
        weight=detail.weight,
        targetWeeklyPoints=detail.targetWeeklyPoints,
        revealedPoints=detail.revealedPoints,
        deficit=detail.deficit,
        creationContribution=detail.creationContribution,
        passiveContribution=detail.passiveContribution,
        driftContribution=detail.driftContribution,
        contributingEvents=[
            LatticeContributor(
                eventId=c.eventId,
                type=c.type,
                timestamp=c.timestamp,
                deltaDays=c.deltaDays,
                baseWeight=c.baseWeight,
                value=c.value,
                decayFactor=c.decayFactor,
                decayedContribution=c.decayedContribution,
                source=c.source,
                simulated=c.simulated,
            )
            for c in detail.contributingEvents
        ],
    )
