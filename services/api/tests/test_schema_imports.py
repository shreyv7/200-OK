from __future__ import annotations

from langgraph.checkpoint.memory import MemorySaver

from app.agents._contracts import CONTRACT_SOURCE
from app.agents._contracts import DecisionPacket, IdentityStack
from app.agents.graphs.coordinator import GRAPH_NODE_ORDER, build_coordinator_graph
from tests.fixtures.sample_data import sample_coordinator_state, sample_decision_packet


def test_schema_contracts_import_cleanly() -> None:
  assert CONTRACT_SOURCE == "mirror"
  packet = sample_decision_packet()
  assert isinstance(packet, DecisionPacket)


def test_identity_stack_import_from_contracts() -> None:
  from app.agents._contracts import IdentityStackElement

  assert IdentityStackElement is not None
  assert IdentityStack is not None
