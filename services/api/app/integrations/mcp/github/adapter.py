"""Fixture GitHub adapter. Owner: Backend. Simulated commits, never a live API call."""

from __future__ import annotations

import uuid
from datetime import datetime

from app.integrations.mcp.base import EvidenceAdapter
from app.schemas.evidence import EvidenceEvent, RawMCPPayload

GITHUB_COMMIT_WEIGHT = 4.0


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
            type="github_commit",
            category="creation",
            identityAttributeIds=raw.get("identityAttributeIds", []),
            value=1.0,
            baseWeight=GITHUB_COMMIT_WEIGHT,
            metadata={"sha": raw.get("sha"), "message": raw.get("message")},
            simulated=True,
        )
