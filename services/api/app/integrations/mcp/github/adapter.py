"""Fixture GitHub adapter. Owner: Backend. Simulated commits, never a live API call."""

from __future__ import annotations

import uuid
from datetime import datetime

from app.integrations.mcp.base import EvidenceAdapter
from app.schemas.evidence import EvidenceEvent, RawMCPPayload
from app.services.identity.scoring.constants import EVENT_WEIGHTS

_TYPE = "github_commit"


class FixtureGithubAdapter(EvidenceAdapter):
    """Maps a commit-shaped fixture payload to a canonical EvidenceEvent."""

    def normalize(self, payload: RawMCPPayload) -> EvidenceEvent:
        raw = payload.rawPayload
        timestamp = raw["timestamp"]
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)

        return EvidenceEvent(
            id=str(uuid.uuid4()),
            userId=raw["userId"],
            timestamp=timestamp,
            source="github",
            type=_TYPE,
            category="creation",
            identityAttributeIds=raw.get("identityAttributeIds", []),
            value=1.0,
            baseWeight=EVENT_WEIGHTS[_TYPE],
            metadata={"sha": raw.get("sha"), "message": raw.get("message")},
            simulated=True,
        )
