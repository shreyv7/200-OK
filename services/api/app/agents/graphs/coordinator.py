from __future__ import annotations

import operator
from typing import Annotated, Any, NotRequired, TypedDict

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
    evidence_id: str | None
    hypothesis_id: str | None
    bottleneck_packet: NotRequired[dict[str, Any] | None]
    knowledge_candidates: NotRequired[list[dict[str, Any]]]
    planner_candidates: NotRequired[list[dict[str, Any]]]
    prior_stack: NotRequired[dict[str, Any] | None]
    identity_stack: NotRequired[dict[str, Any] | None]
    small_experiment: NotRequired[bool]
    delivery_allowed: NotRequired[bool]
    llm_provider: NotRequired[Any]
    search_provider: NotRequired[Any]


GRAPH_NODE_ORDER = [
    "coordinator",
    "knowledge",
    "opportunity",
    "planner",
    "assemble",
    "reflection",
    "coach",
]


def build_coordinator_graph(checkpointer: MemorySaver | None = None):
    """Compile the Coordinator graph with registered nodes."""
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
