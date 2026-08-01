"""Catalog read endpoints. Owner: Backend. F5A/F5B/F5C (prd.md), milestones.md M6."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.di import get_current_user_id, get_db
from app.repositories import catalog_repository
from app.schemas.catalog import GrowthStorySchema, MentorSchema, ToolSchema

router = APIRouter(tags=["catalog"])


@router.get("/catalog/stories", response_model=list[GrowthStorySchema])
def list_stories(
    bottleneck: str | None = None,
    stage: str | None = None,
    db: Session = Depends(get_db),
    _user_id: str = Depends(get_current_user_id),
) -> list[GrowthStorySchema]:
    return catalog_repository.list_stories(db, bottleneck, stage)


@router.get("/catalog/tools", response_model=list[ToolSchema])
def list_tools(
    bottleneck: str | None = None,
    stage: str | None = None,
    db: Session = Depends(get_db),
    _user_id: str = Depends(get_current_user_id),
) -> list[ToolSchema]:
    return catalog_repository.list_tools(db, bottleneck, stage)


@router.get("/catalog/mentors", response_model=list[MentorSchema])
def list_mentors(
    bottleneck: str | None = None,
    stage: str | None = None,
    db: Session = Depends(get_db),
    _user_id: str = Depends(get_current_user_id),
) -> list[MentorSchema]:
    return catalog_repository.list_mentors(db, bottleneck, stage)
