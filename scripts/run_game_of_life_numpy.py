#  Copyright (c) 2026. Programacion Cientifica, DISC, Antofagasta, Chile.
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar

import imageio
import numpy as np
from numba import njit
from prettytable import PrettyTable
from scipy.ndimage import convolve
from tqdm import tqdm

from benchmarking import benchmark  # ty:ignore[unresolved-import]
from logger import configure_logging  # ty:ignore[unresolved-import]


@njit(cache=True)
def evolve_numba(state: np.ndarray) -> np.ndarray:
    # Get the dimensions of the board
    rows, cols = state.shape

    # Create a new board initialized with zeros (all dead cells)
    # This will hold the next generation state
    new_state = np.zeros_like(state)

    # Iterate through every cell on the board
    for r in range(rows):
        for c in range(cols):
            # Initialize neighbor counter for the current cell
            count = 0

            # Check all 8 neighboring cells (3x3 grid centered on current cell)
            for dr in (-1, 0, 1):  # row offset: -1 (above), 0 (same), 1 (below)
                for dc in (-1, 0, 1):  # col offset: -1 (left), 0 (same), 1 (right)
                    # Skip the center cell itself (don't count it as a neighbor)
                    if dr == 0 and dc == 0:
                        continue

                    # Calculate neighbor's coordinates
                    nr, nc = r + dr, c + dc

                    # Only count neighbors that are within board boundaries
                    # This implements edge wrapping prevention (dead cells outside border)
                    if 0 <= nr < rows and 0 <= nc < cols:
                        # Add the neighbor's state (1 if alive, 0 if dead) to the count
                        count += state[nr, nc]

            # Apply Conway's Game of Life rules based on current cell state and neighbor count
            if state[r, c] == 1:
                # Current cell is ALIVE
                # Survival rule: stay alive only if it has 2 or 3 neighbors
                if count == 2 or count == 3:
                    new_state[r, c] = 1
                # Otherwise, the cell dies (new_state stays 0 from initialization)
            else:
                # Current cell is DEAD
                # Birth rule: a dead cell becomes alive only if it has exactly 3 neighbors
                if count == 3:
                    new_state[r, c] = 1
                # Otherwise, the cell stays dead (new_state stays 0)

    # Return the newly computed generation
    return new_state


@dataclass
class GameOfLife:
    """The Game of Life class"""

    # the board
    board: np.ndarray

    # the current generation
    generation: int = 0

    # the max number of generations
    max_generations: int = 10000

    # the representation of a dead cell
    dead_cell: str = "·"

    # the representation of a live cell
    alive_cell: str = "█"

    # constants
    ALIVE: ClassVar[int] = 1
    DEAD: ClassVar[int] = 0

    # kernel to count the neighbors
    KERNEL = np.array(
        [
            [1, 1, 1],
            [1, 0, 1],
            [1, 1, 1],
        ]
    )

    def __post_init__(self) -> None:
        """Post-initialization check for the Game of Life class"""

        # The board needs to be a ndarray
        if not isinstance(self.board, np.ndarray):
            raise TypeError("The board must be a numpy array")

        # The board needs to be a unit8
        if self.board.dtype != np.uint8:
            self.board = self.board.astype(np.uint8)

        # The board needs to be a 2 dimensional array
        if self.board.ndim != 2:
            raise TypeError("The board must be a 2-dimensional array")

        # All the cell in the board needs to be ALIVE/DEAD
        if not np.all(np.isin(self.board, [self.DEAD, self.ALIVE])):
            raise TypeError("The board must contain only zeros or ones")

        # The max generations needs to be positive
        if self.max_generations <= 0:
            raise TypeError("The max_generations must be a positive integer")

    @classmethod
    def from_list(cls, initial_state: list[list[int]]) -> "GameOfLife":
        """Create a GameOfLife class from a list of states"""

        if not initial_state:
            raise TypeError("The initial_state must be a list")

        if not all(isinstance(state, list) for state in initial_state):
            raise ValueError("The initial_state must be a list")

        return cls(board=np.array(initial_state))

    def __str__(self) -> str:
        """Show the board in ascii using PrettyTable."""
        table = PrettyTable()
        table.field_names = [f"Gen={self.generation} -> pop={self.population()}"]

        for r, row in enumerate(self.board):
            str_row = " ".join(
                self.alive_cell if cell == self.ALIVE else self.dead_cell for cell in row
            )
            table.add_row([str_row])
        return str(table)

    def population(self) -> int:
        """Return the population of the board."""
        return np.sum(self.board)

    def expand_board(self) -> None:
        """Expand the board with a border of dead cells."""
        self.board = np.pad(self.board, pad_width=1, mode='constant', constant_values=self.DEAD)

    def compact(self) -> None:
        """Compact the board."""
        rows = np.where(np.any(self.board, axis=1))[0]
        cols = np.where(np.any(self.board, axis=0))[0]
        if rows.size == 0 or cols.size == 0:
            return
        self.board = self.board[rows[0]:rows[-1] + 1, cols[0]:cols[-1] + 1]

    def save_image(self, filename: Path, cell_size: int = 2) -> None:
        """Save the board into a image."""

        # scale up: kronecker product 1 become cell_size x cell_size of 1s.
        arr = np.kron(self.board, np.ones((cell_size, cell_size), dtype=np.uint8))

        # invert the values: 1=black, 0=white
        image = np.where(arr == 1, 0, 255).astype(np.uint8)

        # save image
        imageio.imwrite(filename, image)

    def evolve_optimized(self) -> None:
        # 1) Expand the current board with a 1-cell dead border.
        self.expand_board()

        # 2) Call the numba optimized evolution (machine code compiled)
        self.board = evolve_numba(self.board)

        # DEBUG: try to understand why the evolve_numba cant' parallelized
        # evolve_numba.parallel_diagnostics(level=4)

        # 3) Remove fully dead outer rows/columns to keep the board compact.
        self.compact()

        # 4) Increase generation counter after the full transition is complete.
        self.generation += 1

    def evolve(self) -> None:
        """Advance the board by one generation using Conway's Game of Life rules."""

        # 1) Expand the current board with a 1-cell dead border.
        # - New live cells can appear at the edges.
        # - Without padding, births outside the current bounds would be lost.
        self.expand_board()

        # 2) Count live neighbors for every cell using a convolution kernel.
        # The kernel has 1s around the center and 0 at the center:
        #   [1, 1, 1]
        #   [1, 0, 1]
        #   [1, 1, 1]
        # This sums the 8 surrounding cells while ignoring the cell itself.
        # mode="constant", cval=0 means cells beyond the board are treated as DEAD.
        neighbors = convolve(
            self.board,
            self.KERNEL,
            mode="constant",
            cval=self.DEAD,
        )

        # 3) Build a boolean mask of cells that are currently alive.
        # True  -> currently ALIVE
        # False -> currently DEAD
        alive = self.board == self.ALIVE

        # 4) Apply Conway's rules in vectorized form:
        #
        #   Survival: an ALIVE cell stays alive if it has 2 or 3 neighbors.
        #   Birth:    a DEAD  cell becomes alive if it has exactly 3 neighbors.
        #   Death:    all other cases become/stay dead.
        #
        # We compute each rule as a boolean mask, then combine them.
        survive_mask = alive & ((neighbors == 2) | (neighbors == 3))
        birth_mask = ~alive & (neighbors == 3)  # NOTE: use 3, not 2

        # 5) Create the next generation:
        # - Cells matching survive_mask OR birth_mask become ALIVE (1).
        # - Everything else becomes DEAD (0).
        # Cast back to uint8 to keep board storage compact and consistent.
        self.board = np.where(
            survive_mask | birth_mask,
            self.ALIVE,
            self.DEAD,
        ).astype(np.uint8)

        # 6) Remove fully dead outer rows/columns to keep the board compact.
        # This avoids unbounded growth of empty borders over time.
        self.compact()

        # 7) Increase generation counter after the full transition is complete.
        self.generation += 1


def main():
    # the max number of iterations
    max_iterations = 500

    # init -> board 3x3
    # Glider gun
    board = [
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1],
        [1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1, 1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ]

    # Glider:
    #         [0, 1, 0],
    #         [0, 0, 1],
    #         [1, 1, 1],

    # Original:
    #         [1, 1, 0],
    #         [0, 1, 1],
    #         [0, 1, 0],

    # list[list[int]] -> GameOfLife
    gof = GameOfLife.from_list(board)
    log.debug(f"initial:\n{gof}")

    # iterate over the board and evolve it
    for i in tqdm(range(max_iterations), ncols=250, desc="Gaming"):
        # gof.evolve()
        gof.evolve_optimized()

        # gof.save_image(output_dir / f"board-{i:05d}.png", cell_size=1)
        # log.debug(f"board:\n{gof}")

    log.debug(f"board:\n{gof}")

    # save the last iteration into a png
    gof.save_image(output_dir / f"board-{max_iterations:05d}.png", cell_size=1)


# call the main function
if __name__ == '__main__':
    # configure the logging
    configure_logging(logging.DEBUG)
    # get the main logger
    log = logging.getLogger(__name__)

    # get the root directory
    root_dir = Path(__file__).resolve().parent.parent
    log.debug(f"root_dir: {root_dir}")

    # get the output directory
    output_dir = root_dir / "output"
    log.debug(f"output_dir: {output_dir}")

    # measure time
    with benchmark("main", log):
        log.info("️🏎️ starting ..")
        main()
        log.info("️🏁 done.")
