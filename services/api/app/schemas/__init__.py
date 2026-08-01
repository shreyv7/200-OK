"""Frozen cross-role contracts. Owner: Backend; AIA/AIS consume, propose changes via PR.

Import surface for AIA/AIS: `from app.schemas import EvidenceEvent, DeclaredSelf, ...`
"""

from app.schemas.bottleneck import BottleneckPacket
from app.schemas.catalog import GrowthStorySchema, MentorSchema, ToolSchema
from app.schemas.dashboard import DashboardSummary
from app.schemas.decision import DecisionPacket
from app.schemas.evidence import EvidenceEvent, EvidenceIngestRequest, RawMCPPayload
from app.schemas.gap import AttributeContribution, GapBreakdown
from app.schemas.identity import DeclaredSelf, IdentityAttribute, IdentityMarker
from app.schemas.ledger import LedgerEntry
from app.schemas.lattice import LatticeContributor, LatticeStrutResponse
from app.schemas.onboarding import (
    IdentityPatchRequest,
    OnboardingTurnRequest,
    OnboardingTurnResponse,
)
from app.schemas.stack import IdentityStack, InterventionVariant, StackElement, StackExplanation

__all__ = [
    "BottleneckPacket",
    "GrowthStorySchema",
    "ToolSchema",
    "MentorSchema",
    "DashboardSummary",
    "DecisionPacket",
    "EvidenceEvent",
    "EvidenceIngestRequest",
    "RawMCPPayload",
    "AttributeContribution",
    "GapBreakdown",
    "DeclaredSelf",
    "IdentityAttribute",
    "IdentityMarker",
    "LedgerEntry",
    "LatticeContributor",
    "LatticeStrutResponse",
    "IdentityPatchRequest",
    "OnboardingTurnRequest",
    "OnboardingTurnResponse",
    "IdentityStack",
    "InterventionVariant",
    "StackElement",
    "StackExplanation",
]
