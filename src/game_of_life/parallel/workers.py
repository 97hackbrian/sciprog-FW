"""Worker logic for multiprocessing using shared memory."""

from concurrent.futures import ProcessPoolExecutor
from multiprocessing.shared_memory import SharedMemory

import numpy as np

from game_of_life.config import BoundaryMode
from game_of_life.core.rules import apply_rules, count_neighbors

# Global state for worker processes
_worker_state = {}


def _init_worker(
    shm0_name: str, shm1_name: str, shape: tuple[int, int], boundary_mode: BoundaryMode
) -> None:
    """Initialize worker process with shared memory views."""
    shm0 = SharedMemory(name=shm0_name)
    shm1 = SharedMemory(name=shm1_name)

    array0 = np.ndarray(shape, dtype=np.uint8, buffer=shm0.buf)
    array1 = np.ndarray(shape, dtype=np.uint8, buffer=shm1.buf)

    _worker_state["shm0"] = shm0
    _worker_state["shm1"] = shm1
    _worker_state["array0"] = array0
    _worker_state["array1"] = array1
    _worker_state["shape"] = shape
    _worker_state["boundary_mode"] = boundary_mode


def _compute_chunk(row_start: int, row_end: int, toggle: bool) -> tuple[int, int]:
    """Compute the next generation for a subset of rows, writing directly to shared next_array.

    If toggle is False: read from array0, write to array1.
    If toggle is True: read from array1, write to array0.
    """
    if not toggle:
        current_grid = _worker_state["array0"]
        next_grid = _worker_state["array1"]
    else:
        current_grid = _worker_state["array1"]
        next_grid = _worker_state["array0"]

    shape = _worker_state["shape"]
    boundary_mode = _worker_state["boundary_mode"]

    total_rows = shape[0]
    cols = shape[1]

    # We need a halo of 1 row above and below
    chunk_rows = row_end - row_start
    chunk = np.zeros((chunk_rows + 2, cols), dtype=np.uint8)

    # Copy main chunk
    chunk[1:-1, :] = current_grid[row_start:row_end, :]

    # Halo top
    if row_start > 0:
        chunk[0, :] = current_grid[row_start - 1, :]
    elif boundary_mode == BoundaryMode.TOROIDAL:
        chunk[0, :] = current_grid[total_rows - 1, :]

    # Halo bottom
    if row_end < total_rows:
        chunk[-1, :] = current_grid[row_end, :]
    elif boundary_mode == BoundaryMode.TOROIDAL:
        chunk[-1, :] = current_grid[0, :]

    # Process the chunk
    counts = count_neighbors(chunk, boundary_mode)
    result = apply_rules(chunk, counts)

    # Write the result (without halos) directly to the next grid shared memory
    next_grid[row_start:row_end, :] = result[1:-1, :]

    # Return local statistics for fast aggregation
    active_chunk = next_grid[row_start:row_end, :]
    live_count = int(np.sum(active_chunk))
    dead_count = (chunk_rows * cols) - live_count

    return live_count, dead_count


class WorkerPool:
    """Manages the persistent ProcessPoolExecutor."""

    def __init__(
        self,
        current_name: str,
        next_name: str,
        shape: tuple[int, int],
        boundary_mode: BoundaryMode,
        n_workers: int,
    ):
        self.n_workers = n_workers
        self.executor = ProcessPoolExecutor(
            max_workers=n_workers,
            initializer=_init_worker,
            initargs=(current_name, next_name, shape, boundary_mode),
        )
        self.shape = shape
        self.toggle = False

    def compute_generation(self) -> tuple[int, int]:
        """Dispatch chunked work to the pool and return (total_live, total_dead)."""
        rows = self.shape[0]
        chunk_size = max(1, rows // self.n_workers)

        futures = []
        for i in range(self.n_workers):
            start = i * chunk_size
            end = rows if i == self.n_workers - 1 else (i + 1) * chunk_size
            if start < rows:
                futures.append(self.executor.submit(_compute_chunk, start, end, self.toggle))

        total_live = 0
        total_dead = 0
        for f in futures:
            live, dead = f.result()
            total_live += live
            total_dead += dead

        # Flip toggle for the next generation
        self.toggle = not self.toggle
        return total_live, total_dead

    def shutdown(self) -> None:
        """Shutdown the executor."""
        self.executor.shutdown(wait=True)
