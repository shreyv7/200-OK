"""Identity Evolution proposal persistence. Owner: Backend. milestones.md M7 (F11)."""

from __future__ import annotations

from sqlalchemy import select

from app.models.identity_evolution import IdentityEvolutionProposalModel
from app.schemas.agent_run import IdentityEvolutionProposal
from app.schemas.identity import IdentityAttribute


def _to_schema(row: IdentityEvolutionProposalModel) -> IdentityEvolutionProposal:
    return IdentityEvolutionProposal(
        id=row.id,
        userId=row.user_id,
        proposedAttributes=[IdentityAttribute.model_validate(a) for a in row.proposed_attributes],
        citedEvidenceIds=row.cited_evidence_ids,
        rationale=row.rationale,
        status=row.status,
        createdAt=row.created_at,
    )


def create(
    db,
    user_id: str,
    proposed_attributes: list[IdentityAttribute],
    cited_evidence_ids: list[str],
    rationale: str,
) -> IdentityEvolutionProposal:
    row = IdentityEvolutionProposalModel(
        user_id=user_id,
        proposed_attributes=[a.model_dump(mode="json") for a in proposed_attributes],
        cited_evidence_ids=cited_evidence_ids,
        rationale=rationale,
        status="pending",
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
        IdentityEvolutionProposalModel.user_id == user_id
    )
    return db.scalar(stmt) is not None


def set_status(db, row: IdentityEvolutionProposalModel, status: str) -> IdentityEvolutionProposal:
    row.status = status
    db.commit()
    db.refresh(row)
    return _to_schema(row)
