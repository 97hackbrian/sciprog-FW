"""Rule evaluation and neighbor counting for the Game of Life."""

import numpy as np
from scipy.ndimage import convolve
from typeguard import typechecked

from game_of_life.config import BoundaryMode

# 3x3 kernel, center is 0 so a cell does not count itself as a neighbor
NEIGHBOR_KERNEL: np.ndarray = np.array(
    [
        [1, 1, 1],
        [1, 0, 1],
        [1, 1, 1],
    ],
    dtype=np.uint8,
)


@typechecked
def count_neighbors(grid_array: np.ndarray, boundary: BoundaryMode) -> np.ndarray:
    """Count live neighbors for each cell in the grid."""
    if boundary == BoundaryMode.TOROIDAL:
        mode = "wrap"
        cval = 0  # unused for wrap
    else:
        mode = "constant"
        cval = 0

    return convolve(grid_array, NEIGHBOR_KERNEL, mode=mode, cval=cval)


@typechecked
def apply_rules(grid_array: np.ndarray, neighbor_counts: np.ndarray) -> np.ndarray:
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
    return np.where(survive | birth, 1, 0).astype(np.uint8)
