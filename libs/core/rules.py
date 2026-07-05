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
