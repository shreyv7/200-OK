"""Catalog tables: Growth Stories, Tools, Mentors. Owner: Backend. milestones.md M6 (F5A-C)."""

from __future__ import annotations

from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class GrowthStoryModel(Base):
    __tablename__ = "growth_stories"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str] = mapped_column(String)
    author: Mapped[str] = mapped_column(String)
    summary: Mapped[str] = mapped_column(String)
    outcome: Mapped[str] = mapped_column(String)
    identity_tags: Mapped[list] = mapped_column(JSON, default=list)
    stage_tags: Mapped[list] = mapped_column(JSON, default=list)
    bottleneck_tags: Mapped[list] = mapped_column(JSON, default=list)


class ToolModel(Base):
    __tablename__ = "tools"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(String)
    url: Mapped[str] = mapped_column(String)
    starter_action: Mapped[str] = mapped_column(String)
    stage_tags: Mapped[list] = mapped_column(JSON, default=list)
    bottleneck_tags: Mapped[list] = mapped_column(JSON, default=list)


class MentorModel(Base):
    __tablename__ = "mentors"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    journey: Mapped[str] = mapped_column(String)
    strengths: Mapped[list] = mapped_column(JSON, default=list)
    stage_tags: Mapped[list] = mapped_column(JSON, default=list)
    bottleneck_tags: Mapped[list] = mapped_column(JSON, default=list)
