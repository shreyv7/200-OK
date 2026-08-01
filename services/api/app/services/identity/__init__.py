"""Identity service package."""

from app.services.identity.sanitizer import (
    SanitizedEvent,
    validate_and_sanitize_event,
)
from app.services.identity.enrichment import (
    KEYWORD_ATTRIBUTE_MAP,
    enrich_event,
)
from app.services.identity.aggregates import (
    AttributeAggregate,
    RevealedSelfAggregates,
    build_revealed_aggregates,
)
from app.services.identity.twin import (
    DigitalTwinReadModel,
    assemble_digital_twin,
)

__all__ = [
    "SanitizedEvent",
    "validate_and_sanitize_event",
    "KEYWORD_ATTRIBUTE_MAP",
    "enrich_event",
    "AttributeAggregate",
    "RevealedSelfAggregates",
    "build_revealed_aggregates",
    "DigitalTwinReadModel",
    "assemble_digital_twin",
]
