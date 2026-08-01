"""Identity Evolution proposal persistence. Owner: Backend. milestones.md M7/M8 (F11)."""

from __future__ import annotations

from sqlalchemy import select

from app.models.identity_evolution import IdentityEvolutionProposalModel
from app.schemas.evolution import IdentityEvolutionProposal, ProposedChange


def _to_schema(row: IdentityEvolutionProposalModel) -> IdentityEvolutionProposal:
    return IdentityEvolutionProposal(
        proposalId=row.id,
        userId=row.user_id,
        declaredSelfVersion=row.declared_self_version,
        proposedChanges=[ProposedChange.model_validate(c) for c in row.proposed_changes],
        supportingEvidenceIds=row.supporting_evidence_ids,
        narrative=row.narrative,
        generatedAt=row.generated_at,
    )


def create(db, proposal: IdentityEvolutionProposal) -> IdentityEvolutionProposal:
    row = IdentityEvolutionProposalModel(
        id=proposal.proposalId,
        user_id=proposal.userId,
        declared_self_version=proposal.declaredSelfVersion,
        proposed_changes=[c.model_dump(mode="json") for c in proposal.proposedChanges],
        supporting_evidence_ids=proposal.supportingEvidenceIds,
        narrative=proposal.narrative,
        status="pending",
        generated_at=proposal.generatedAt,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _to_schema(row)


def get(db, proposal_id: str) -> tuple[IdentityEvolutionProposalModel, IdentityEvolutionProposal] | None:
    row = db.get(IdentityEvolutionProposalModel, proposal_id)
    if row is None:
        return None
    return row, _to_schema(row)


def has_pending_for_user(db, user_id: str) -> bool:
    stmt = select(IdentityEvolutionProposalModel.id).where(
        IdentityEvolutionProposalModel.user_id == user_id,
        IdentityEvolutionProposalModel.status == "pending",
    )
    return db.scalar(stmt) is not None


def set_status(db, row: IdentityEvolutionProposalModel, status: str) -> IdentityEvolutionProposal:
    row.status = status
    db.commit()
    db.refresh(row)
    return _to_schema(row)
