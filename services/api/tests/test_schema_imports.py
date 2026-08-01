from __future__ import annotations

from langgraph.checkpoint.memory import MemorySaver

from app.agents.contract_source import CONTRACT_SOURCE
from app.agents.graphs.coordinator import GRAPH_NODE_ORDER, build_coordinator_graph
from app.schemas import DecisionPacket, IdentityStack, StackElement
from tests.fixtures.sample_data import sample_coordinator_state, sample_decision_packet


def test_schema_contracts_import_cleanly() -> None:
    assert CONTRACT_SOURCE == "app.schemas"
    packet = sample_decision_packet()
    assert isinstance(packet, DecisionPacket)


def test_identity_stack_import_from_schemas() -> None:
    assert StackElement is not None
    assert IdentityStack is not None
