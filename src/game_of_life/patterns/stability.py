"""Stability and cycle detection for the Game of Life."""

import logging

import numpy as np
from typeguard import typechecked

log = logging.getLogger(__name__)


@typechecked
class StabilityTracker:
    """Tracks stability (exact stasis) of the simulation."""

    def __init__(self) -> None:
        pass

    def check(self, previous: np.ndarray, current: np.ndarray) -> bool:
        """Return True if the simulation has reached an exact stasis (no changes)."""
        is_stable = bool(np.array_equal(previous, current))
        if is_stable:
            log.info("Simulation reached stable state (exact stasis).")
        return is_stable

    def reset(self) -> None:
        """Reset the tracker."""
        pass


@typechecked
class CycleTracker:
    """Tracks periodic cycles purely as a DEBUG-level diagnostic."""

    def __init__(self, capacity: int = 16):
        self.capacity = capacity
        self.history: list[bytes] = []

    def check_and_log(self, current: np.ndarray) -> None:
        """Check if the current state exists in recent history and log it."""
        # Using bytes instead of hash() as ndarray is unhashable,
        # and we need actual content comparison, bytes of uint8 array is reliable.
        current_hash = current.tobytes()

        try:
            # Search from newest to oldest to find the shortest period first
            # self.history is ordered oldest to newest, so we reverse it
            idx = self.history[::-1].index(current_hash)
            period = idx + 1
            log.debug(f"Periodic cycle detected: period {period}")
        except ValueError:
            pass

        self.history.append(current_hash)
        if len(self.history) > self.capacity:
            self.history.pop(0)

    def reset(self) -> None:
        """Reset the cycle history."""
        self.history.clear()
