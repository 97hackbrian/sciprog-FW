"""Loader for Game of Life initial states."""

import pickle
from pathlib import Path

import numpy as np
from typeguard import typechecked


@typechecked
def load_initial_state(path: Path) -> np.ndarray:
    """Load a Game of Life initial state from a pickle file.
    
    Expects either:
    1. A raw 2D numpy array (values 0 and 1).
    2. A dictionary containing the grid under common keys like 'grid', 'board', 'state'.
    
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the payload is invalid or cannot be parsed as a 2D array.
    """
    if not path.exists():
        raise FileNotFoundError(f"Initial state file not found: {path}")

    with open(path, "rb") as f:
        payload = pickle.load(f)

    grid = None

    if isinstance(payload, np.ndarray):
        grid = payload
    elif isinstance(payload, dict):
        for key in ("grid", "board", "state"):
            if key in payload and isinstance(payload[key], np.ndarray):
                grid = payload[key]
                break

    if grid is None:
        raise ValueError(
            "Invalid pickle payload. Expected a 2D numpy array or a dict "
            "containing a 2D numpy array under 'grid', 'board', or 'state'."
        )

    if grid.ndim != 2:
        raise ValueError(f"Expected a 2D numpy array, got {grid.ndim}D.")

    # Ensure it's uint8 with 0s and 1s
    if grid.dtype != np.uint8:
        grid = grid.astype(np.uint8)

    if not np.all(np.isin(grid, [0, 1])):
        raise ValueError("Grid array must contain only 0s and 1s.")

    return grid
