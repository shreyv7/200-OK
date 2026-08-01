"""Rule-based evidence enrichment module for AIA.

Maps incoming raw/sanitized events to identityAttributeIds and calculates initial a_ik scores.
"""

from typing import Dict, List, Optional
from app.services.identity.sanitizer import SanitizedEvent

# Rule keyword map for MVP rule-based enrichment
KEYWORD_ATTRIBUTE_MAP: Dict[str, List[str]] = {
    "public_speaker": ["speak", "speech", "talk", "presentation", "toastmaster", "audience", "pitch"],
    "builder": ["build", "code", "commit", "github", "project", "ship", "dev", "repo", "publish"],
}


def enrich_event(event: SanitizedEvent, known_attribute_ids: Optional[List[str]] = None) -> SanitizedEvent:
    """Enriches event by inferring attr_id and assigning applicability score a_ik.
    
    If attr_id is already assigned and valid, retains it.
    Otherwise applies keyword rules against event metadata/type.
    """
    if event.attr_id and event.attr_id != "unmapped":
        return event

    text_content = f"{event.event_type} {event.metadata.get('title', '')} {event.metadata.get('description', '')}".lower()
    
    inferred_attr_id = "unmapped"
    inferred_a_ik = event.a_ik

    for attr_id, keywords in KEYWORD_ATTRIBUTE_MAP.items():
        if any(kw in text_content for kw in keywords):
            inferred_attr_id = attr_id
            inferred_a_ik = 1.0
            break

    # If still unmapped but known attributes provided, assign to first known attribute with 0.5 applicability
    if inferred_attr_id == "unmapped" and known_attribute_ids:
        inferred_attr_id = known_attribute_ids[0]
        inferred_a_ik = 0.5

    event.attr_id = inferred_attr_id
    event.a_ik = inferred_a_ik

    return event
