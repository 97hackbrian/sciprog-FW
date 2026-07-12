"""Dispatcher for adaptive multiprocessing."""

import atexit
from typing import Any, Protocol

import numpy as np
from typeguard import typechecked

from libs.config import BoundaryMode, SimulationConfig
from libs.core.rules import apply_rules, count_neighbors
from libs.parallel.shared_grid import SharedGridBuffer
from libs.parallel.workers import WorkerPool


@typechecked
def _compute_stats(array: Any, is_gpu: bool = False) -> tuple[int, int]:
    """Helper to compute live and dead cell counts."""
    if is_gpu:
        import cupy as cp  # type: ignore

        live = int(cp.sum(array))
    else:
        live = int(np.sum(array))

    dead = int(array.size - live)
    return live, dead


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
        live, dead = _compute_stats(next_arr, is_gpu=False)
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

        live, dead = _compute_stats(self.gpu_array, is_gpu=True)

        # Transfer back to CPU memory for the rest of the app
        next_arr = cp.asnumpy(self.gpu_array)

        return next_arr, live, dead

    def shutdown(self) -> None:
        """No special resources to release for GPU (handled by CuPy)."""
        pass


@typechecked
class NumbaDispatcher:
    """Numba JIT-compiled CPU strategy using multi-threading."""

    def __init__(self, boundary_mode: BoundaryMode):
        self.boundary_mode = boundary_mode

    def step(self, grid_array: np.ndarray) -> tuple[np.ndarray, int, int]:
        """Compute next generation using Numba JIT."""
        from libs.core.rules import numba_step_bounded, numba_step_toroidal

        if self.boundary_mode == BoundaryMode.TOROIDAL:
            next_arr = numba_step_toroidal(grid_array)
        else:
            next_arr = numba_step_bounded(grid_array)

        live, dead = _compute_stats(next_arr, is_gpu=False)
        return next_arr, live, dead

    def shutdown(self) -> None:
        """No special resources to release for Numba."""
        pass


@typechecked
def get_dispatcher(
    shape: tuple[int, int], config: SimulationConfig, initial: np.ndarray
) -> Dispatcher:
    """Return the appropriate dispatcher based on config and grid size."""
    import logging

    from libs.config import ComputeBackend

    logger = logging.getLogger(__name__)

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
        try:
            return GpuDispatcher(config, initial)
        except Exception as e:
            logger.warning(
                f"Failed to initialize GPU dispatcher: {e}. Falling back to CPU Numba backend."
            )
            config.backend = ComputeBackend.NUMBA

    if config.backend == ComputeBackend.NUMBA:
        try:
            return NumbaDispatcher(config.boundary_mode)
        except Exception as e:
            logger.warning(
                f"Failed to initialize Numba dispatcher: {e}. Falling back to CPU SciPy backend."
            )
            config.backend = ComputeBackend.CPU

    total_cells = shape[0] * shape[1]
    if total_cells < config.multiprocessing_threshold_cells:
        return SingleProcessDispatcher(config.boundary_mode)
    else:
        return MultiprocessDispatcher(shape, config, initial)
