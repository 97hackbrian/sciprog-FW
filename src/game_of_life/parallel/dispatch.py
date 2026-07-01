"""Dispatcher for adaptive multiprocessing."""

import atexit
from typing import Protocol

import numpy as np
from typeguard import typechecked

from game_of_life.config import BoundaryMode, SimulationConfig
from game_of_life.core.rules import apply_rules, count_neighbors
from game_of_life.parallel.shared_grid import SharedGridBuffer
from game_of_life.parallel.workers import WorkerPool


class Dispatcher(Protocol):
    def step(self, grid_array: np.ndarray) -> tuple[np.ndarray, int, int]:
        ...
        
    def shutdown(self) -> None:
        ...


@typechecked
class SingleProcessDispatcher:
    """Standard single-process strategy."""
    
    def __init__(self, boundary_mode: BoundaryMode):
        self.boundary_mode = boundary_mode
        
    def step(self, grid_array: np.ndarray) -> tuple[np.ndarray, int, int]:
        counts = count_neighbors(grid_array, self.boundary_mode)
        next_arr = apply_rules(grid_array, counts)
        live = int(np.sum(next_arr))
        dead = next_arr.size - live
        return next_arr, live, dead
        
    def shutdown(self) -> None:
        pass


@typechecked
class MultiprocessDispatcher:
    """Multiprocess strategy using shared memory."""
    
    def __init__(self, shape: tuple[int, int], config: SimulationConfig, initial: np.ndarray):
        self.buffer = SharedGridBuffer(shape)
        self.buffer.load(initial)
        self.boundary_mode = config.boundary_mode
        
        self.pool = WorkerPool(
            current_name=self.buffer.current_shm.name,
            next_name=self.buffer.next_shm.name,
            shape=shape,
            boundary_mode=config.boundary_mode,
            n_workers=config.n_workers
        )
        
        # Ensure cleanup if process exits unexpectedly
        atexit.register(self.shutdown)
        
    def step(self, grid_array: np.ndarray) -> tuple[np.ndarray, int, int]:
        # Perform computation
        live, dead = self.pool.compute_generation()
        
        # Swap main process references
        self.buffer.swap()
        
        # Ensure the engine's grid array also points to the new current array
        # Note: we return self.buffer.current_array as the new state for the engine
        # and copy it to grid_array just in case
        np.copyto(grid_array, self.buffer.current_array)
        
        return self.buffer.current_array, live, dead
        
    def shutdown(self) -> None:
        """Shutdown pool and unlink shared memory."""
        atexit.unregister(self.shutdown)
        self.pool.shutdown()
        self.buffer.close()
        # ONLY the owning process unlinks!
        self.buffer.unlink()


@typechecked
def get_dispatcher(shape: tuple[int, int], config: SimulationConfig, initial: np.ndarray) -> Dispatcher:
    """Return the appropriate dispatcher based on grid size."""
    total_cells = shape[0] * shape[1]
    if total_cells < config.multiprocessing_threshold_cells:
        return SingleProcessDispatcher(config.boundary_mode)
    else:
        return MultiprocessDispatcher(shape, config, initial)
