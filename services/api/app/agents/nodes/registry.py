from __future__ import annotations

from typing import Callable

from app.agents.nodes.coach.node import coach_node
from app.agents.nodes.coordinator.node import coordinator_node
from app.agents.nodes.knowledge.node import knowledge_node
from app.agents.nodes.opportunity.node import opportunity_node
from app.agents.nodes.planner.node import planner_node
from app.agents.nodes.reflection.node import reflection_node

NodeFn = Callable[[dict], dict]

NODE_REGISTRY: dict[str, NodeFn] = {
  "coordinator": coordinator_node,
  "knowledge": knowledge_node,
  "opportunity": opportunity_node,
  "planner": planner_node,
  "reflection": reflection_node,
  "coach": coach_node,
}
