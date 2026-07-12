"""Rule evaluation and neighbor counting for the Game of Life."""

from typing import Any

import numpy as np
from scipy.ndimage import convolve  # type: ignore[import-untyped]
from typeguard import typechecked

from libs.config import BoundaryMode

try:
    import cupy as cp  # type: ignore
    from cupyx.scipy.ndimage import convolve as cp_convolve  # type: ignore
except ImportError:
    cp = None
    cp_convolve = None

try:
    import numba as nb  # type: ignore
except ImportError:
    nb = None

# 3x3 kernel, center is 0 so a cell does not count itself as a neighbor
NEIGHBOR_KERNEL_CPU: np.ndarray = np.array(
    [
        [1, 1, 1],
        [1, 0, 1],
        [1, 1, 1],
    ],
    dtype=np.uint8,
)
NEIGHBOR_KERNEL_GPU: Any = cp.array(NEIGHBOR_KERNEL_CPU) if cp is not None else None


@typechecked
def count_neighbors(grid_array: Any, boundary: BoundaryMode) -> Any:
    """Count live neighbors for each cell in the grid."""
    if boundary == BoundaryMode.TOROIDAL:
        mode = "wrap"
        cval = 0  # unused for wrap
    else:
        mode = "constant"
        cval = 0

    if cp is not None and isinstance(grid_array, cp.ndarray):
        return cp_convolve(grid_array, NEIGHBOR_KERNEL_GPU, mode=mode, cval=cval)
    else:
        return convolve(grid_array, NEIGHBOR_KERNEL_CPU, mode=mode, cval=cval)


@typechecked
def apply_rules(grid_array: Any, neighbor_counts: Any) -> Any:
    """Apply Conway's Game of Life rules to produce the next generation.

    1. Any live cell with fewer than two live neighbors dies (underpopulation).
    2. Any live cell with two or three live neighbors survives.
    3. Any live cell with more than three live neighbors dies (overpopulation).
    4. Any dead cell with exactly three live neighbors becomes a live cell (reproduction).
    """
    alive = grid_array == 1

    # Rule 2: survival
    survive = alive & ((neighbor_counts == 2) | (neighbor_counts == 3))

    # Rule 4: birth
    birth = ~alive & (neighbor_counts == 3)

    # Rule 1 & 3: death is implied by not surviving
    if cp is not None and isinstance(grid_array, cp.ndarray):
        return cp.where(survive | birth, 1, 0).astype(cp.uint8)
    else:
        return np.where(survive | birth, 1, 0).astype(np.uint8)


# --- Numba Implementations ---

if nb is not None:

    @nb.njit(parallel=True, fastmath=True)
    def numba_step_toroidal(grid: np.ndarray) -> np.ndarray:
        """Compute the next generation using Numba on CPU with toroidal boundary."""
        rows, cols = grid.shape
        next_grid = np.zeros_like(grid)
        for r in nb.prange(rows):
            for c in range(cols):
                live_neighbors = 0
                for i in range(-1, 2):
                    for j in range(-1, 2):
                        if i == 0 and j == 0:
                            continue
                        rr = (r + i) % rows
                        cc = (c + j) % cols
                        live_neighbors += grid[rr, cc]

                is_alive = grid[r, c] == 1
                if is_alive and (live_neighbors == 2 or live_neighbors == 3):
                    next_grid[r, c] = 1
                elif not is_alive and live_neighbors == 3:
                    next_grid[r, c] = 1
        return next_grid

    @nb.njit(parallel=True, fastmath=True)
    def numba_step_bounded(grid: np.ndarray) -> np.ndarray:
        """Compute the next generation using Numba on CPU with bounded boundary."""
        rows, cols = grid.shape
        next_grid = np.zeros_like(grid)
        for r in nb.prange(rows):
            for c in range(cols):
                live_neighbors = 0
                for i in range(-1, 2):
                    for j in range(-1, 2):
                        if i == 0 and j == 0:
                            continue
                        rr = r + i
                        cc = c + j
                        if 0 <= rr < rows and 0 <= cc < cols:
                            live_neighbors += grid[rr, cc]

                is_alive = grid[r, c] == 1
                if is_alive and (live_neighbors == 2 or live_neighbors == 3):
                    next_grid[r, c] = 1
                elif not is_alive and live_neighbors == 3:
                    next_grid[r, c] = 1
        return next_grid
else:

    def numba_step_toroidal(grid: np.ndarray) -> np.ndarray:
        """Fallback for when numba is not installed."""
        raise ImportError("Numba is not installed")

    def numba_step_bounded(grid: np.ndarray) -> np.ndarray:
        """Fallback for when numba is not installed."""
        raise ImportError("Numba is not installed")
