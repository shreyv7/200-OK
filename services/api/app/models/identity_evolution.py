"""Identity Evolution proposal table. Owner: Backend. milestones.md M7/M8 (F11).

Mirrors AIA's app.schemas.evolution.IdentityEvolutionProposal shape
(proposed_changes is the add/remove/reweight diff, not a flat attribute
replacement). `status` is Backend-only bookkeeping for accept/reject —
not part of AIA's frozen generation-output schema.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class IdentityEvolutionProposalModel(Base):
    __tablename__ = "identity_evolution_proposals"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), index=True)
    declared_self_version: Mapped[int] = mapped_column(Integer)
    proposed_changes: Mapped[list] = mapped_column(JSON, default=list)
    supporting_evidence_ids: Mapped[list] = mapped_column(JSON, default=list)
    narrative: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="pending")
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
