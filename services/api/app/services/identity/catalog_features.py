"""Catalog features extractor and optional embedding trigger for M6 AIA.

Derives stage, bottleneck_label, bottleneck_confidence, and top_deficit_attr_id
deterministically for AIS catalog ranking (Growth Stories, Tools, Mentors).
"""

from typing import Any, List, Optional

from app.schemas.identity import DeclaredSelf
from app.services.decision.packet import BottleneckCandidate, CatalogFeatures
from app.services.identity.scoring.gap import GapResult


def get_stage_from_gap(gap_score: int) -> str:
    """Maps Gap score (0-100) to deterministic stage tier for catalog ranking.
    
    0-25: peak
    26-50: advancing
    51-75: developing
    76-100: early
    """
    if gap_score <= 25:
        return "peak"
    elif gap_score <= 50:
        return "advancing"
    elif gap_score <= 75:
        return "developing"
    return "early"


def extract_catalog_features(
    gap_result: GapResult,
    bottleneck_candidates: Optional[List[BottleneckCandidate]] = None,
) -> CatalogFeatures:
    """Extracts catalog ranking features deterministically from GapResult and bottleneck candidates."""
    stage = get_stage_from_gap(gap_result.gap_score)

    top_candidate = bottleneck_candidates[0] if bottleneck_candidates else None
    bottleneck_label = top_candidate.label if top_candidate else ""
    bottleneck_confidence = top_candidate.confidence if top_candidate else 0.0

    top_deficit_attr = ""
    if gap_result.per_attribute:
        worst_attr = max(gap_result.per_attribute, key=lambda a: a.deficit)
        top_deficit_attr = worst_attr.attr_id

    return CatalogFeatures(
        stage=stage,
        bottleneck_label=bottleneck_label,
        bottleneck_confidence=bottleneck_confidence,
        top_deficit_attr_id=top_deficit_attr,
    )


def trigger_identity_embedding(
    declared_self: DeclaredSelf,
    embedding_provider: Optional[Any] = None,
) -> Optional[List[float]]:
    """Triggers optional identity summary embedding via EmbeddingProvider facade if available."""
    if not embedding_provider or not hasattr(embedding_provider, "embed"):
        return None

    try:
        attr_ids = [attr.id for attr in declared_self.attributes]
        summary_text = f"Identity targets: {', '.join(attr_ids)}"
        vectors = embedding_provider.embed([summary_text])
        if vectors and isinstance(vectors, list) and len(vectors) > 0:
            return vectors[0]
        return None
    except Exception:
        return None
