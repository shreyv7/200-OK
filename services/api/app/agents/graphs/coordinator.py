from __future__ import annotations

import operator
from typing import Annotated, Any, TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from app.agents.nodes.registry import NODE_REGISTRY


class CoordinatorState(TypedDict):
  trigger: str
  run_id: str
  user_id: str
  decision_packet: dict[str, Any]
  stack_draft: dict[str, Any] | None
  visited: Annotated[list[str], operator.add]


GRAPH_NODE_ORDER = [
  "coordinator",
  "knowledge",
  "opportunity",
  "planner",
  "reflection",
  "coach",
]


def build_coordinator_graph(checkpointer: MemorySaver | None = None):
  """Compile the M0 Coordinator shell with registered no-op nodes."""
  graph = StateGraph(CoordinatorState)

  for name in GRAPH_NODE_ORDER:
      graph.add_node(name, NODE_REGISTRY[name])

  graph.add_edge(START, "coordinator")
  for current, nxt in zip(GRAPH_NODE_ORDER, GRAPH_NODE_ORDER[1:]):
      graph.add_edge(current, nxt)
  graph.add_edge("coach", END)

  if checkpointer is not None:
      return graph.compile(checkpointer=checkpointer)
  return graph.compile()
