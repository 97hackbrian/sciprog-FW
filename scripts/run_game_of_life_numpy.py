#  Copyright (c) 2026. Programacion Cientifica, DISC, Antofagasta, Chile.
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar

import numpy as np
from prettytable import PrettyTable
from scipy.ndimage import convolve
from tqdm import tqdm

from benchmarking import benchmark  # ty:ignore[unresolved-import]
from logger import configure_logging  # ty:ignore[unresolved-import]


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
        table.field_names = [f"Generation nº {self.generation} -> pop={self.population()}"]

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

    def evolve(self) -> None:
        """Evolve the board."""

        # expand the board 1 row/col around the board
        self.expand_board()

        # apply the convolve over the board
        neighbors = convolve(
            self.board,
            self.KERNEL,
            mode="constant",
            cval=self.DEAD,
        )

        # determine which cells are alive?
        alive = self.board == self.ALIVE

        # apply the rules of Game of Life
        self.board = np.where(
            (alive & ((neighbors == 2) | (neighbors == 3))) | (~alive & (neighbors == 2)), self.ALIVE, self.DEAD,
        ).astype(np.uint8)

        # compact the board
        self.compact()

        # increments the generation
        self.generation += 1

        # create a new board of the same size of board with all values in cero
        # next_board = np.zeros_like(self.board, dtype=np.uint8)


def main():
    # the max number of iterations
    max_iterations = 500

    # init -> board 3x3
    board = [
        [1, 1, 0],
        [0, 1, 1],
        [0, 1, 0],
    ]

    # list[list[int]] -> GameOfLife
    gof = GameOfLife.from_list(board)
    log.debug(f"initial:\n{gof}")

    # iterate over the board and evolve it
    for i in tqdm(range(max_iterations), ncols=180, desc="Gaming"):
        gof.evolve()
        # log.debug(f"board:\n{gof}")

    # log.debug(f"board:\n{gof}")


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
