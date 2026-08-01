"""Weekly Report + Identity Evolution wiring. Owner: Backend. milestones.md M7/M8 (F8/F11).

M8 fix: this module originally hand-rolled its own prompt formatting
against Backend-local duplicate schemas. AIA shipped real, complete
generation logic (generate_weekly_report, propose_identity_evolution)
in the same M7 merge — this module now just supplies their real inputs
(DeclaredSelf, evidence window, GapResult) and calls them directly, per
guidelines.md role isolation (AIA owns the reasoning; Backend owns
persistence/wiring).
"""

from __future__ import annotations

from app.providers.llm.base import LLMProvider
from app.repositories import evolution_repository
from app.schemas.evolution import IdentityEvolutionProposal, ProposedChange
from app.schemas.identity import IdentityAttribute
from app.schemas.report import WeeklyReport
from app.services.identity import orchestration
from app.services.identity.evolution_agent import propose_identity_evolution
from app.services.identity.weekly_report import generate_weekly_report as _generate_weekly_report


def generate_weekly_report(db, llm_provider: LLMProvider, user_id: str) -> WeeklyReport | None:
    result = orchestration.recompute_and_persist(db, user_id, llm_provider=llm_provider)
    if result is None:
        return None

    return _generate_weekly_report(
        user_id=user_id,
        declared_self=result.declared_self,
        events=result.events,
        gap_result=result.gap_result,
        prior_gap_score=result.prior_gap_score,
        llm_provider=llm_provider,
    )


def generate_evolution_proposal(
    db, llm_provider: LLMProvider, user_id: str
) -> IdentityEvolutionProposal | None:
    result = orchestration.recompute_and_persist(db, user_id, llm_provider=llm_provider)
    if result is None:
        return None

    proposal = propose_identity_evolution(
        user_id=user_id,
        declared_self=result.declared_self,
        events=result.events,
        gap_result=result.gap_result,
        llm_provider=llm_provider,
    )
    if proposal is None:
        return None

    return evolution_repository.create(db, proposal)


def apply_proposed_changes(
    current_attributes: list[IdentityAttribute], changes: list[ProposedChange]
) -> list[IdentityAttribute]:
    """Applies an add/remove/reweight diff against the current Declared
    Self's attributes — never a flat replace (M8 fix: the original M7
    accept endpoint replaced the whole attribute list, silently dropping
    anything not mentioned in the proposal)."""
    by_id = {a.id: a for a in current_attributes}

    for change in changes:
        if change.action == "remove":
            by_id.pop(change.attributeId, None)
        elif change.action == "reweight":
            existing = by_id.get(change.attributeId)
            if existing is not None and change.newWeight is not None:
                by_id[change.attributeId] = existing.model_copy(update={"weight": change.newWeight})
        elif change.action == "add":
            by_id[change.attributeId] = IdentityAttribute(
                id=change.attributeId,
                label=change.attributeLabel,
                weight=change.newWeight if change.newWeight is not None else 0.1,
                targetWeeklyPoints=15.0,
                markers=[],
            )

    return list(by_id.values())
