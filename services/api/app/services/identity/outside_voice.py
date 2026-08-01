"""Outside Voice Lens evaluator for AIA M8 (P2).

Constrained to 5 pre-approved growth domains to propose identity expansion lenses
only when primary attribute alignment is high (>= 70%).
"""

from dataclasses import dataclass
from typing import List, Optional

from app.schemas.identity import DeclaredSelf
from app.services.identity.scoring.gap import GapResult

ALLOWED_DOMAINS: List[str] = [
    "public_speaking",
    "software_building",
    "writing",
    "networking",
    "mindfulness",
]


@dataclass
class OutsideVoiceRecommendation:
    domain: str
    reason: str
    suggested_lens: str


def evaluate_outside_voice_lens(
    declared_self: DeclaredSelf,
    gap_result: GapResult,
) -> Optional[OutsideVoiceRecommendation]:
    """Evaluates cross-domain Outside Voice lens recommendation if alignment >= 70%."""
    # Only propose outside voice expansion if primary alignment is strong
    if gap_result.alignment < 70:
        return None

    existing_attrs = {attr.id for attr in declared_self.attributes}
    unassigned_domains = [d for d in ALLOWED_DOMAINS if d not in existing_attrs]

    if not unassigned_domains:
        return None

    target_domain = unassigned_domains[0]
    domain_labels = {
        "public_speaking": "Public Speaking & Communication",
        "software_building": "Software Construction & Shipping",
        "writing": "Thought Leadership & Writing",
        "networking": "Community & Professional Networking",
        "mindfulness": "Mindfulness & Focus Discipline",
    }

    label = domain_labels.get(target_domain, target_domain.replace("_", " ").title())

    return OutsideVoiceRecommendation(
        domain=target_domain,
        reason=f"Strong alignment ({gap_result.alignment}%) across core identity. Ready to explore Outside Voice lens: {label}.",
        suggested_lens=f"OutsideVoice_{target_domain}",
    )
