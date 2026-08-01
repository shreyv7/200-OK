"""Identity Evolution proposal table. Owner: Backend. milestones.md M7 (F11)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class IdentityEvolutionProposalModel(Base):
    __tablename__ = "identity_evolution_proposals"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), index=True)
    proposed_attributes: Mapped[list] = mapped_column(JSON, default=list)
    cited_evidence_ids: Mapped[list] = mapped_column(JSON, default=list)
    rationale: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
