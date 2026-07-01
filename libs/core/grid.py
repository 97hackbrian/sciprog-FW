"""Grid representation for Conway's Game of Life."""

from dataclasses import dataclass
from typing import ClassVar

import numpy as np
from typeguard import typechecked

from libs.config import BoundaryMode


@typechecked
@dataclass
class Grid:
    """A 2D cellular automaton grid.

    Values are strictly 0 (dead) and 1 (alive), stored as uint8.
    """

    array: np.ndarray
    boundary_mode: BoundaryMode = BoundaryMode.TOROIDAL

    ALIVE: ClassVar[int] = 1
    DEAD: ClassVar[int] = 0

    def __post_init__(self) -> None:
        """Validate the grid array."""
        if self.array.ndim != 2:
            raise ValueError(f"Grid array must be 2D, got {self.array.ndim}D")

        if self.array.dtype != np.uint8:
            self.array = self.array.astype(np.uint8)

        if not np.all(np.isin(self.array, [self.DEAD, self.ALIVE])):
            raise ValueError("Grid array must contain only 0s and 1s")

    @property
    def rows(self) -> int:
        """Number of rows in the grid."""
        return int(self.array.shape[0])

    @property
    def cols(self) -> int:
        """Number of columns in the grid."""
        return int(self.array.shape[1])

    def population(self) -> int:
        """Return the number of live cells."""
        return int(float(np.sum(self.array)))

    def dead_cells(self) -> int:
        """Return the number of dead cells."""
        return self.rows * self.cols - self.population()
