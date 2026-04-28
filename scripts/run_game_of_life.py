#  Copyright (c) 2026. Programacion Cientifica, DISC, Antofagasta, Chile.
import logging

from prettytable import PrettyTable, HRuleStyle

from benchmarking import benchmark  # ty:ignore[unresolved-import]
from logger import configure_logging  # ty:ignore[unresolved-import]


def show_board(board):
    """Show the board in the screen in a human readable format."""
    table = PrettyTable()
    table.header = False
    table.hrules = HRuleStyle.ALL
    for row in board:
        table.add_row([
            "█" if cell == 1 else "·" for cell in row
        ])
    log.debug(f"\n{table}")


def count_neighbours(board, row, column):
    """Count the number of neighbouring cells in the board."""
    sum = 0
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
                sum += 1

    return sum


def evolve(board):
    """Evolve the board."""

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

    return next_board


def main():
    """The main function."""
    max_iterations = 10

    # init -> board 3x3
    board = [
        [0, 1, 0],
        [1, 1, 0],
        [1, 0, 1],
    ]

    # show the initial state
    show_board(board)

    for i in range(max_iterations):
        log.debug(f"-- iteration: {i + 1} {'-' * 60}")
        board = evolve(board)
        show_board(board)


# call the main function
if __name__ == '__main__':
    # configure the logging
    configure_logging(logging.DEBUG)
    # get the main logger
    log = logging.getLogger(__name__)
    # measure time
    with benchmark("main", log):
        log.info("️🏎️ starting ..")
        main()
        log.info("️🏁 done.")
