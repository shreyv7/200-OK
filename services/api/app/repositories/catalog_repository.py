"""Catalog persistence/read. Owner: Backend. milestones.md M6.

Tag matching done in Python over a full fetch — catalog is tiny
(~25-30 rows), avoids Postgres/SQLite JSON-containment dialect
divergence in tests (see anvi/plan-m6-backend.md Open Question 2).
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.catalog import GrowthStoryModel, MentorModel, ToolModel
from app.schemas.catalog import GrowthStorySchema, MentorSchema, ToolSchema


def _matches(tags: list[str], filter_value: str | None) -> bool:
    return filter_value is None or filter_value in tags


def list_stories(
    db: Session, bottleneck: str | None = None, stage: str | None = None
) -> list[GrowthStorySchema]:
    rows = db.scalars(select(GrowthStoryModel))
    return [
        GrowthStorySchema(
            id=r.id,
            title=r.title,
            author=r.author,
            summary=r.summary,
            outcome=r.outcome,
            identityTags=r.identity_tags,
            stageTags=r.stage_tags,
            bottleneckTags=r.bottleneck_tags,
        )
        for r in rows
        if _matches(r.bottleneck_tags, bottleneck) and _matches(r.stage_tags, stage)
    ]


def list_tools(
    db: Session, bottleneck: str | None = None, stage: str | None = None
) -> list[ToolSchema]:
    rows = db.scalars(select(ToolModel))
    return [
        ToolSchema(
            id=r.id,
            name=r.name,
            description=r.description,
            url=r.url,
            starterAction=r.starter_action,
            stageTags=r.stage_tags,
            bottleneckTags=r.bottleneck_tags,
        )
        for r in rows
        if _matches(r.bottleneck_tags, bottleneck) and _matches(r.stage_tags, stage)
    ]


def list_mentors(
    db: Session, bottleneck: str | None = None, stage: str | None = None
) -> list[MentorSchema]:
    rows = db.scalars(select(MentorModel))
    return [
        MentorSchema(
            id=r.id,
            name=r.name,
            journey=r.journey,
            strengths=r.strengths,
            stageTags=r.stage_tags,
            bottleneckTags=r.bottleneck_tags,
        )
        for r in rows
        if _matches(r.bottleneck_tags, bottleneck) and _matches(r.stage_tags, stage)
    ]
