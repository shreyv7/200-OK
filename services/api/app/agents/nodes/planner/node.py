from __future__ import annotations

from typing import Any


def planner_node(state: dict[str, Any]) -> dict[str, Any]:
  return {"visited": ["planner"]}
