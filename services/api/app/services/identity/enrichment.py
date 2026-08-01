"""Rule-based evidence enrichment module for AIA.

Enriches Backend EvidenceEvent objects by populating identityAttributeIds based on keyword/category rules.
"""

from typing import Dict, List, Optional
from app.schemas.evidence import EvidenceEvent
from app.schemas.identity import DeclaredSelf

KEYWORD_ATTRIBUTE_MAP: Dict[str, List[str]] = {
    "public_speaker": ["speak", "speech", "talk", "presentation", "toastmaster", "audience", "pitch"],
    "builder": ["build", "code", "commit", "github", "project", "ship", "dev", "repo", "publish"],
}


def enrich_evidence_event(event: EvidenceEvent, declared_self: Optional[DeclaredSelf] = None) -> EvidenceEvent:
    """Enriches EvidenceEvent by populating identityAttributeIds if unmapped.
    
    If identityAttributeIds is already non-empty, retains existing mappings.
    Otherwise applies keyword rules against event type and metadata.
    """
    if event.identityAttributeIds:
        return event

    text_content = f"{event.type} {event.metadata.get('title', '')} {event.metadata.get('description', '')}".lower()
    inferred_ids: List[str] = []

    for attr_id, keywords in KEYWORD_ATTRIBUTE_MAP.items():
        if any(kw in text_content for kw in keywords):
            inferred_ids.append(attr_id)

    # Fallback to first attribute of DeclaredSelf if unmapped
    if not inferred_ids and declared_self and declared_self.attributes:
        inferred_ids.append(declared_self.attributes[0].id)

    event.identityAttributeIds = inferred_ids
    return event
