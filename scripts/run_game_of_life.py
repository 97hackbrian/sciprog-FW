#  Copyright (c) 2026. Programacion Cientifica, DISC, Antofagasta, Chile.
import logging
from pathlib import Path
from typing import TypeAlias

import imageio
import numpy as np
from prettytable import PrettyTable, HRuleStyle
from tqdm import tqdm

from benchmarking import benchmark
from logger import configure_logging

# The board.
Board: TypeAlias = list[list[int]]


def show_board(board: Board) -> None:
    """Show the board in the screen in a human readable format."""
    table = PrettyTable()

    # number of colunmns
    ncols = len(board[0]) if board else 0

    # header
    table.field_names = ["r\\c"] + [str(c) for c in range(ncols)]
    table.hrules = HRuleStyle.ALL

    # populate the table
    for r, row in enumerate(board):
        table.add_row([str(r)] + ["█" if cell == 1 else "·" for cell in row])
    log.debug(f"\n{table}")


def count_neighbours(board: Board, row: int, column: int) -> int:
    """Count the number of neighbouring cells in the board."""
    total = 0

    # iterate over the 3x3 square around the cell
    for r in (range(row - 1, row + 2)):
        for c in (range(column - 1, column + 2)):

            # the center cell can't be counted
            if r == row and c == column:
                continue

            # outside the board by row
            if r < 0 or r >= len(board):
                continue

            # outside the board by col
            if c < 0 or c >= len(board[r]):
                continue

            # count only the living cellsl
            if board[r][c] == 1:
                total += 1

    return total


def expand(board: Board) -> Board:
    """Expand the board so that all cells are neighbours."""
    n_rows = len(board)
    n_cols = len(board[0])

    # the board expanded
    expanded_board = []
    for r in range(n_rows + 2):
        # create the new row
        new_row = []
        for c in range(n_cols + 2):
            # append each cell into the row
            new_row.append(0)
        # append to the new board the new row
        expanded_board.append(new_row)

    # copy the center board
    for r in range(n_rows):
        for c in range(n_cols):
            expanded_board[r + 1][c + 1] = board[r][c]

    return expanded_board


def compact(board: Board) -> Board:
    """Compact the board."""

    # 1. remove the first row if all the values are zero
    if all(c == 0 for c in board[0]):
        # splice the first row
        board = board[1:]

    # 2. remove the last row if all the values are zero
    if all(c == 0 for c in board[-1]):
        # splice the last row
        board = board[0:-1]

    # 3. remove the first col if all the values are zero
    if all(row[0] == 0 for row in board):
        for row in board:
            row.pop(0)

    # 4. remove the last col if all the values are zero
    if all(row[-1] == 0 for row in board):
        for row in board:
            row.pop(-1)

    return board


def evolve(board: Board) -> Board:
    """Evolve the board."""

    # expand the board
    board = expand(board)

    # create a new board of the same size of board with all values in cero
    next_board = [[0] * len(row) for row in board]

    # iterate over the whole board
    for row in range(len(board)):
        for column in range(len(board[row])):

            # count the neighbours
            neighbours = count_neighbours(board, row, column)
            # log.debug(f"neighbours: {row},{column} -> {neighbours}")

            # it's alive!
            if board[row][column] == 1:
                # 1. survival
                if neighbours == 2 or neighbours == 3:
                    next_board[row][column] = 1
                    continue
                # 2. death by isolation
                if neighbours < 2:
                    next_board[row][column] = 0
                    continue
                # 3. death by overcrowding
                if neighbours > 3:
                    next_board[row][column] = 0
            else:
                # it's dead!
                if neighbours == 3:
                    next_board[row][column] = 1

    # remove the borders with all values in zero
    next_board = compact(next_board)

    return next_board


def save_board(board: Board, filename: Path, cell_size: int = 2) -> None:
    """Save the board into a image."""

    # list[list[int]] to numpy of uint8 (0 -> 255)
    arr = np.array(board, dtype=np.uint8)

    # scale up: kronecker product 1 become cell_size x cell_size of 1s.
    arr = np.kron(arr, np.ones((cell_size, cell_size), dtype=np.uint8))

    # invert the values: 1=black, 0=white
    image = np.where(arr == 1, 0, 255).astype(np.uint8)

    # save image
    imageio.imwrite(filename, image)


def main() -> None:
    """The main function."""

    # the max number of iterations
    max_iterations = 500

    # init -> board 3x3
    board = [
        [1, 1, 0],
        [0, 1, 1],
        [0, 1, 0],
    ]

    # show the initial state
    show_board(board)

    # iterate over the board and evolve it
    for i in tqdm(range(max_iterations), ncols=180, desc="Gaming"):
        # log.debug(f"-- iteration: {i + 1} {'-' * 60}")
        board = evolve(board)

        # save the board into a image
        save_board(board, output_dir / f"board-{i:05d}.png", cell_size=10)

    # show the last state
    show_board(board)


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
