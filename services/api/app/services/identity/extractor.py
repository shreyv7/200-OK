"""Extraction validation and schema repair pass module for AIA.

Validates LLM extracted DeclaredSelf dictionary and applies auto-repair pass
(normalizing weights to sum exactly to 1.0, assigning default target points D_i).
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Union

from app.schemas.identity import DeclaredSelf, IdentityAttribute, IdentityMarker
from app.services.identity.scoring.constants import DEFAULT_DECLARED_TARGET


def validate_and_repair_extraction(
    raw: Union[Dict[str, Any], DeclaredSelf],
    user_id: str,
) -> Tuple[bool, Optional[DeclaredSelf], Optional[str]]:
    """Validates raw extracted identity data and applies weight auto-repair pass.
    
    Ensures sum(w_i) == 1.0 and sets confirmedAt = None (unconfirmed until user confirms).
    """
    if isinstance(raw, DeclaredSelf):
        raw_dict = raw.model_dump()
    elif isinstance(raw, dict):
        raw_dict = raw
    else:
        return False, None, "Extraction payload must be a dictionary or DeclaredSelf model"

    raw_attrs = raw_dict.get("attributes", [])
    if not isinstance(raw_attrs, list) or not raw_attrs:
        return False, None, "Extraction payload contains no valid attributes"

    parsed_attributes: List[IdentityAttribute] = []
    total_w = 0.0

    for idx, attr_data in enumerate(raw_attrs):
        if not isinstance(attr_data, dict):
            continue

        attr_id = str(attr_data.get("id") or f"attr_{idx + 1}")
        label = str(attr_data.get("label") or f"Attribute {idx + 1}")
        w_i = float(attr_data.get("weight", 1.0 / len(raw_attrs)))
        w_i = max(0.01, w_i)
        total_w += w_i

        d_i = float(attr_data.get("targetWeeklyPoints") or attr_data.get("declared_weekly_target") or DEFAULT_DECLARED_TARGET)
        if d_i <= 0:
            d_i = DEFAULT_DECLARED_TARGET

        raw_markers = attr_data.get("markers", [])
        parsed_markers: List[IdentityMarker] = []
        if isinstance(raw_markers, list):
            for m_idx, m_data in enumerate(raw_markers):
                if isinstance(m_data, dict):
                    m_id = str(m_data.get("id") or f"m_{attr_id}_{m_idx + 1}")
                    m_label = str(m_data.get("label") or f"Marker {m_idx + 1}")
                    m_desc = str(m_data.get("description", "")) if m_data.get("description") else None
                    parsed_markers.append(IdentityMarker(id=m_id, label=m_label, description=m_desc))

        parsed_attributes.append(
            IdentityAttribute(
                id=attr_id,
                label=label,
                weight=w_i,
                targetWeeklyPoints=d_i,
                markers=parsed_markers,
            )
        )

    if not parsed_attributes:
        return False, None, "Failed to parse any valid attributes"

    # Weight auto-repair: normalize weights so sum(w_i) == 1.0
    if total_w > 0:
        normalized_attrs: List[IdentityAttribute] = []
        running_w = 0.0
        for i, attr in enumerate(parsed_attributes):
            if i == len(parsed_attributes) - 1:
                norm_w = round(1.0 - running_w, 4)
            else:
                norm_w = round(attr.weight / total_w, 4)
                running_w += norm_w
            
            normalized_attrs.append(
                IdentityAttribute(
                    id=attr.id,
                    label=attr.label,
                    weight=norm_w,
                    targetWeeklyPoints=attr.targetWeeklyPoints,
                    markers=attr.markers,
                )
            )
        parsed_attributes = normalized_attrs

    now = datetime.now(timezone.utc)
    version = int(raw_dict.get("version", 1))
    decl_id = str(raw_dict.get("id") or f"decl_{user_id}_v{version}")

    repaired_declared_self = DeclaredSelf(
        id=decl_id,
        userId=user_id,
        version=version,
        attributes=parsed_attributes,
        createdAt=now,
        confirmedAt=None,  # Safety: unconfirmed until explicit consent
    )

    return True, repaired_declared_self, None
