"""Declared Self extraction schemas and TypedDict models.

Target for Gemini structured output during Mirror Interview (M3).
"""

from typing import TypedDict, List
import json


class IdentityMarker(TypedDict):
    id: str
    label: str
    description: str
    observable_examples: List[str]


class IdentityAttribute(TypedDict):
    id: str
    label: str
    description: str
    weight: float
    markers: List[IdentityMarker]
    declared_weekly_target: float


class DeclaredSelf(TypedDict):
    version: int
    user_id: str
    attributes: List[IdentityAttribute]
    confirmed: bool
    created_at: str


def validate_weights(attributes: List[IdentityAttribute], tolerance: float = 1e-6) -> bool:
    """Asserts that the sum of attribute weights is approximately 1.0."""
    if not attributes:
        return False
    total_weight = sum(attr["weight"] for attr in attributes)
    return abs(total_weight - 1.0) < tolerance


def get_declared_self_json_schema() -> dict:
    """Returns a JSON Schema dictionary suitable for LLM structured output targets."""
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "DeclaredSelf",
        "type": "object",
        "properties": {
            "version": {"type": "integer"},
            "user_id": {"type": "string"},
            "confirmed": {"type": "boolean"},
            "created_at": {"type": "string"},
            "attributes": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "label": {"type": "string"},
                        "description": {"type": "string"},
                        "weight": {"type": "number"},
                        "declared_weekly_target": {"type": "number"},
                        "markers": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "string"},
                                    "label": {"type": "string"},
                                    "description": {"type": "string"},
                                    "observable_examples": {
                                        "type": "array",
                                        "items": {"type": "string"}
                                    }
                                },
                                "required": ["id", "label", "description", "observable_examples"]
                            }
                        }
                    },
                    "required": ["id", "label", "description", "weight", "declared_weekly_target", "markers"]
                }
            }
        },
        "required": ["version", "user_id", "attributes", "confirmed", "created_at"]
    }
