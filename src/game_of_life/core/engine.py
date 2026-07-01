"""Simulation engine for Conway's Game of Life."""

import time
from dataclasses import dataclass
from typing import Any

import numpy as np
from typeguard import typechecked

from game_of_life.config import SimulationConfig
from game_of_life.core.grid import Grid

# Note: multiprocessing and pattern detection will be integrated in later phases.
# We will use structural typing or import dynamically for them to avoid circular imports
# or coupling before they are built.


@typechecked
@dataclass(frozen=True)
class StepResult:
    """Result of a single generation step."""

    iteration: int
    live_cells: int
    dead_cells: int
    execution_time_ms: float
    is_stable: bool
    detected_patterns: list[Any]  # Placeholder for PatternMatch


@typechecked
class SimulationEngine:
    """The core engine that runs the simulation."""

    def __init__(self, config: SimulationConfig, initial: np.ndarray):
        """Initialize the engine with config and initial state."""
        self.config = config
        self.iteration = 0
        self.grid = Grid(array=initial.copy(), boundary_mode=config.boundary_mode)

        # Initialize logic modules
        from game_of_life.parallel.dispatch import get_dispatcher
        from game_of_life.patterns.detector import PatternDetector
        from game_of_life.patterns.stability import CycleTracker, StabilityTracker

        self.dispatcher = get_dispatcher(initial.shape, config, initial)
        self.stability_tracker = StabilityTracker()
        self.cycle_tracker = CycleTracker()
        self.pattern_detector = PatternDetector(
            enable_extended_catalog=config.enable_extended_pattern_catalog
        )

    def reset(self, initial: np.ndarray) -> None:
        """Reset the simulation to a new initial state."""
        self.iteration = 0
        self.grid = Grid(array=initial.copy(), boundary_mode=self.config.boundary_mode)

        if self.stability_tracker:
            self.stability_tracker.reset()
        if self.cycle_tracker:
            self.cycle_tracker.reset()

        # Also need to reset the dispatcher if it's multiprocess
        from game_of_life.parallel.dispatch import get_dispatcher

        if self.dispatcher:
            self.dispatcher.shutdown()
        self.dispatcher = get_dispatcher(initial.shape, self.config, initial)

    def step(self) -> StepResult:
        """Compute the next generation."""
        start_ns = time.perf_counter_ns()

        next_array, live_cells, dead_cells = self.dispatcher.step(self.grid.array)

        # Check stability
        is_stable = self.stability_tracker.check(self.grid.array, next_array)
        self.cycle_tracker.check_and_log(next_array)

        # Detect patterns
        patterns = []
        if self.iteration % self.config.pattern_detection_interval == 0:
            patterns = self.pattern_detector.detect(next_array)

        # Update state
        self.grid.array = next_array
        self.iteration += 1

        elapsed_ms = (time.perf_counter_ns() - start_ns) / 1_000_000.0

        return StepResult(
            iteration=self.iteration,
            live_cells=live_cells,
            dead_cells=dead_cells,
            execution_time_ms=elapsed_ms,
            is_stable=is_stable,
            detected_patterns=patterns,
        )
