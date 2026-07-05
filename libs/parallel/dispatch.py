"""Dispatcher for adaptive multiprocessing."""

import atexit
from typing import Protocol

import numpy as np
from typeguard import typechecked

from libs.config import BoundaryMode, SimulationConfig
from libs.core.rules import apply_rules, count_neighbors
from libs.parallel.shared_grid import SharedGridBuffer
from libs.parallel.workers import WorkerPool


class Dispatcher(Protocol):
    """Protocol for simulation dispatchers (single or multiprocess)."""

    def step(self, grid_array: np.ndarray) -> tuple[np.ndarray, int, int]:
        """Compute the next generation and return the new grid array, live, and dead counts."""
        ...

    def shutdown(self) -> None:
        """Release resources used by the dispatcher."""
        ...


@typechecked
class SingleProcessDispatcher:
    """Standard single-process strategy."""

    def __init__(self, boundary_mode: BoundaryMode):
        self.boundary_mode = boundary_mode

    def step(self, grid_array: np.ndarray) -> tuple[np.ndarray, int, int]:
        """Compute next generation using a single process."""
        counts = count_neighbors(grid_array, self.boundary_mode)
        next_arr = apply_rules(grid_array, counts)
        live = int(np.sum(next_arr))
        dead = next_arr.size - live
        return next_arr, live, dead

    def shutdown(self) -> None:
        """No resources to release for single process."""
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
            n_workers=config.n_workers,
        )

        # Ensure cleanup if process exits unexpectedly
        atexit.register(self.shutdown)

    def step(self, grid_array: np.ndarray) -> tuple[np.ndarray, int, int]:
        """Compute next generation using multiprocessing pool."""
        # Perform computation
        live, dead = self.pool.compute_generation()

        # Swap main process references
        self.buffer.swap()

        return self.buffer.current_array, live, dead

    def shutdown(self) -> None:
        """Shutdown pool and unlink shared memory."""
        atexit.unregister(self.shutdown)
        self.pool.shutdown()
        self.buffer.close()
        # ONLY the owning process unlinks!
        self.buffer.unlink()


@typechecked
class GpuDispatcher:
    """GPU-accelerated strategy using CuPy."""

    def __init__(self, config: SimulationConfig, initial: np.ndarray):
        import cupy as cp  # type: ignore

        self.boundary_mode = config.boundary_mode
        self.gpu_array = cp.array(initial)

    def step(self, grid_array: np.ndarray) -> tuple[np.ndarray, int, int]:
        """Compute next generation using GPU."""
        import cupy as cp  # type: ignore

        counts = count_neighbors(self.gpu_array, self.boundary_mode)
        self.gpu_array = apply_rules(self.gpu_array, counts)

        live = int(cp.sum(self.gpu_array))
        dead = int(self.gpu_array.size - live)

        # Transfer back to CPU memory for the rest of the app
        next_arr = cp.asnumpy(self.gpu_array)

        return next_arr, live, dead

    def shutdown(self) -> None:
        """No special resources to release for GPU (handled by CuPy)."""
        pass


@typechecked
def get_dispatcher(
    shape: tuple[int, int], config: SimulationConfig, initial: np.ndarray
) -> Dispatcher:
    """Return the appropriate dispatcher based on config and grid size."""
    from libs.config import ComputeBackend

    use_gpu = False
    if config.backend == ComputeBackend.GPU:
        use_gpu = True
    elif config.backend == ComputeBackend.AUTO:
        try:
            import cupy as cp  # type: ignore

            if cp.cuda.runtime.getDeviceCount() > 0:
                use_gpu = True
        except Exception:
            pass

    if use_gpu:
        return GpuDispatcher(config, initial)

    total_cells = shape[0] * shape[1]
    if total_cells < config.multiprocessing_threshold_cells:
        return SingleProcessDispatcher(config.boundary_mode)
    else:
        return MultiprocessDispatcher(shape, config, initial)
