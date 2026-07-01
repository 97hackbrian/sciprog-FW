"""Tests for stability and cycle detection."""

import numpy as np

from game_of_life.patterns.stability import CycleTracker, StabilityTracker


def test_stability_tracker() -> None:
    """Exact-match stop condition fires on true still life, not on Blinker."""
    tracker = StabilityTracker()
    
    # True still life (Block)
    block_current = np.array([
        [0, 0, 0, 0],
        [0, 1, 1, 0],
        [0, 1, 1, 0],
        [0, 0, 0, 0],
    ], dtype=np.uint8)
    
    block_next = block_current.copy()
    
    # Should fire because it's identical
    assert tracker.check(block_current, block_next) is True
    
    # Blinker
    blinker_state1 = np.array([
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 1, 1, 1, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
    ], dtype=np.uint8)
    
    blinker_state2 = np.array([
        [0, 0, 0, 0, 0],
        [0, 0, 1, 0, 0],
        [0, 0, 1, 0, 0],
        [0, 0, 1, 0, 0],
        [0, 0, 0, 0, 0],
    ], dtype=np.uint8)
    
    # Should NOT fire because it oscillates
    assert tracker.check(blinker_state1, blinker_state2) is False


def test_cycle_tracker(caplog) -> None:
    """Cycle tracker reports period 2 for a Blinker without stopping the simulation."""
    import logging
    caplog.set_level(logging.DEBUG)
    
    tracker = CycleTracker()
    
    blinker_state1 = np.array([
        [0, 0, 0],
        [1, 1, 1],
        [0, 0, 0],
    ], dtype=np.uint8)
    
    blinker_state2 = np.array([
        [0, 1, 0],
        [0, 1, 0],
        [0, 1, 0],
    ], dtype=np.uint8)
    
    tracker.check_and_log(blinker_state1)
    tracker.check_and_log(blinker_state2)
    tracker.check_and_log(blinker_state1)  # Cycle should be detected here
    
    assert any("Periodic cycle detected: period 2" in record.message for record in caplog.records)
