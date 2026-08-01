"""In-memory active stack registry and invalidation flags (M2).

Backend stack persistence lands in M4; this module exposes a safe seam for
dashboard reads and the Growth Decision Engine consumer.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.schemas import DecisionPacket, IdentityStack


@dataclass
class ActiveStackFlags:
    userId: str
    invalidate: bool = False
    invalidatedElementIds: list[str] = field(default_factory=list)
    hypothesisId: str | None = None
    hasActiveStack: bool = False


_active_stacks: dict[str, IdentityStack | None] = {}
_active_flags: dict[str, ActiveStackFlags] = {}


def clear_stack_state() -> None:
    """Test helper — reset in-memory registry."""
    _active_stacks.clear()
    _active_flags.clear()


def set_active_stack(user_id: str, stack: IdentityStack | None) -> None:
    _active_stacks[user_id] = stack
    flags = _active_flags.get(user_id)
    if flags is None:
        _active_flags[user_id] = ActiveStackFlags(
            userId=user_id,
            hasActiveStack=stack is not None,
            hypothesisId=stack.hypothesisId if stack is not None else None,
        )
    else:
        flags.hasActiveStack = stack is not None
        flags.hypothesisId = stack.hypothesisId if stack is not None else None


def get_active_stack(user_id: str) -> IdentityStack | None:
    return _active_stacks.get(user_id)


def get_active_stack_flags(user_id: str) -> ActiveStackFlags:
    if user_id not in _active_flags:
        _active_flags[user_id] = ActiveStackFlags(userId=user_id)
    return _active_flags[user_id]


def apply_invalidation(user_id: str, packet: DecisionPacket) -> ActiveStackFlags:
    """Apply DecisionPacket invalidation to active stack flags (empty stack OK)."""
    stack = get_active_stack(user_id)
    invalidated_ids: list[str] = list(packet.invalidatedElementIds)
    if packet.invalidateStack and stack is not None and not invalidated_ids:
        invalidated_ids = [element.id for element in stack.elements]

    flags = get_active_stack_flags(user_id)
    flags.invalidate = packet.invalidateStack
    flags.invalidatedElementIds = invalidated_ids
    flags.hasActiveStack = stack is not None
    flags.hypothesisId = stack.hypothesisId if stack is not None else flags.hypothesisId
    return flags


def get_active_stack_or_safe(user_id: str) -> tuple[IdentityStack | None, ActiveStackFlags]:
    """Dashboard-safe read: never raises when no stack exists."""
    return get_active_stack(user_id), get_active_stack_flags(user_id)
