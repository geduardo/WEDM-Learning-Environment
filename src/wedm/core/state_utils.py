from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .state import EDMState


def is_short_circuited(state: EDMState) -> bool:
    """Checks if a short-circuit condition exists in the given state.

    A short circuit is currently defined as the wire position being greater
    than or equal to the workpiece position. This can be expanded in the
    future to include other causes, such as debris accumulation.

    Args:
        state: The current EDMState object.

    Returns:
        True if a short-circuit condition exists, False otherwise.
    """
    return state.wire_position >= state.workpiece_position
