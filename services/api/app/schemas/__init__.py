"""Frozen cross-role contracts. Owner: Backend; AIA/AIS consume, propose changes via PR.

Import surface for AIA/AIS: `from app.schemas import EvidenceEvent, DeclaredSelf, ...`
"""

from app.schemas.bottleneck import BottleneckPacket
from app.schemas.decision import DecisionPacket
from app.schemas.evidence import EvidenceEvent, EvidenceIngestRequest, RawMCPPayload
from app.schemas.gap import AttributeContribution, GapBreakdown
from app.schemas.identity import DeclaredSelf, IdentityAttribute, IdentityMarker
from app.schemas.ledger import LedgerEntry
from app.schemas.stack import IdentityStack, InterventionVariant, StackElement, StackExplanation

__all__ = [
    "BottleneckPacket",
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
    "IdentityStack",
    "InterventionVariant",
    "StackElement",
    "StackExplanation",
]
