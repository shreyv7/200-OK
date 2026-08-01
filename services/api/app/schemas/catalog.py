"""Catalog contracts (Growth Stories, Tools, Mentors). Owner: Backend. milestones.md M6."""

from __future__ import annotations

from pydantic import BaseModel


class GrowthStorySchema(BaseModel):
    id: str
    title: str
    author: str
    summary: str
    outcome: str
    identityTags: list[str]
    stageTags: list[str]
    bottleneckTags: list[str]


class ToolSchema(BaseModel):
    id: str
    name: str
    description: str
    url: str
    starterAction: str
    stageTags: list[str]
    bottleneckTags: list[str]


class MentorSchema(BaseModel):
    id: str
    name: str
    journey: str
    strengths: list[str]
    stageTags: list[str]
    bottleneckTags: list[str]
