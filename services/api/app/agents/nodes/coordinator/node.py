from __future__ import annotations

from typing import Any


def _noop_node(name: str):
  def node(state: dict[str, Any]) -> dict[str, Any]:
      return {"visited": [name]}

  return node


coordinator_node = _noop_node("coordinator")
