"""EvidenceAdapter interface. Owner: Backend adapters + seed fixtures (prd.md §7).

Each provider implements only `normalize()`. The simulator and seed script
invoke adapters with fixtures; they never construct EvidenceEvent directly.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.schemas.evidence import EvidenceEvent, RawMCPPayload


class EvidenceAdapter(ABC):
    @abstractmethod
    def normalize(self, payload: RawMCPPayload) -> EvidenceEvent:
        raise NotImplementedError
