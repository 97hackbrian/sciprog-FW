"""Tests for Game of Life rules and core engine behavior."""

import numpy as np
import pytest

from libs.config import BoundaryMode, SimulationConfig
from libs.core.engine import SimulationEngine
from libs.core.rules import count_neighbors
from libs.patterns.catalog import CATALOG, PatternCategory


def naive_count_neighbors_toroidal(grid: np.ndarray) -> np.ndarray:
    """A pure np.roll based neighbor counting implementation for cross-validation."""
    counts = np.zeros_like(grid, dtype=np.uint8)
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            shifted = np.roll(grid, shift=(dr, dc), axis=(0, 1))
            counts += shifted
    return counts


def test_rule_implementation_cross_validation() -> None:
    """Cross-validate scipy.ndimage.convolve against pure np.roll on random boards."""
    np.random.seed(42)
    for _ in range(10):
        # Generate random 50x50 board
        board = np.random.choice([0, 1], size=(50, 50), p=[0.8, 0.2]).astype(np.uint8)

        # Scipy convolve implementation
        scipy_counts = count_neighbors(board, BoundaryMode.TOROIDAL)

        # Naive np.roll implementation
        naive_counts = naive_count_neighbors_toroidal(board)

        # They must match exactly
        np.testing.assert_array_equal(scipy_counts, naive_counts)


def run_pattern_for_period(
    cells: frozenset[tuple[int, int]],
    period: int,
    expected_cells: int,
    check_translation: bool = False,
) -> None:
    """Helper to run a pattern for its period and verify behavior."""
    if not cells:
        return

    # Find bounding box
    min_r = min(r for r, c in cells)
    max_r = max(r for r, c in cells)
    min_c = min(c for r, c in cells)
    max_c = max(c for r, c in cells)

    # Create a grid large enough to avoid boundary effects
    # For spaceships, they translate, so we need extra space
    grid_size = max(max_r - min_r, max_c - min_c) + 20 + period * 2
    initial = np.zeros((grid_size, grid_size), dtype=np.uint8)

    # Place pattern in center
    offset_r = grid_size // 2 - min_r
    offset_c = grid_size // 2 - min_c

    for r, c in cells:
        initial[r + offset_r, c + offset_c] = 1

    config = SimulationConfig(boundary_mode=BoundaryMode.TOROIDAL)
    engine = SimulationEngine(config=config, initial=initial)

    for _ in range(period):
        engine.step()

    # Verify population
    assert engine.grid.population() == expected_cells

    # Get the resulting active cells
    result_cells = {
        (r, c) for r in range(grid_size) for c in range(grid_size) if engine.grid.array[r, c] == 1
    }

    if check_translation:
        # Spaceships should have the exact same shape, but translated
        # Normalize both to origin
        orig_min_r = min(r for r, c in cells)
        orig_min_c = min(c for r, c in cells)
        norm_orig = {(r - orig_min_r, c - orig_min_c) for r, c in cells}

        res_min_r = min(r for r, c in result_cells)
        res_min_c = min(c for r, c in result_cells)
        norm_res = {(r - res_min_r, c - res_min_c) for r, c in result_cells}

        assert norm_orig == norm_res, "Spaceship shape deformed"
    else:
        # Oscillators and still lifes should return to EXACTLY the initial coordinates
        # (accounting for the offset we added)
        expected_coords = {(r + offset_r, c + offset_c) for r, c in cells}
        assert result_cells == expected_coords, "Pattern did not return to initial state"


@pytest.mark.parametrize("pattern_name", ["Block", "Beehive", "Loaf", "Boat", "Tub"])
def test_still_lifes(pattern_name: str) -> None:
    """Still lifes should remain unchanged after 1 generation."""
    # Find pattern
    pattern = next((p for p in CATALOG if p.name == pattern_name), None)
    assert pattern is not None
    assert pattern.category == PatternCategory.STILL_LIFE

    run_pattern_for_period(
        pattern.cells, period=1, expected_cells=len(pattern.cells), check_translation=False
    )


@pytest.mark.parametrize("pattern_name", ["Blinker", "Toad", "Beacon", "Pulsar", "Pentadecathlon"])
def test_oscillators(pattern_name: str) -> None:
    """Oscillators should return to their exact initial state after their period."""
    pattern = next((p for p in CATALOG if p.name == pattern_name), None)
    assert pattern is not None
    assert pattern.category == PatternCategory.OSCILLATOR
    assert pattern.period is not None

    run_pattern_for_period(
        pattern.cells,
        period=pattern.period,
        expected_cells=len(pattern.cells),
        check_translation=False,
    )


@pytest.mark.parametrize("pattern_name", ["Glider", "LWSS", "MWSS", "HWSS"])
def test_spaceships(pattern_name: str) -> None:
    """Spaceships should return to their initial shape after their period (but translated)."""
    pattern = next((p for p in CATALOG if p.name == pattern_name), None)
    assert pattern is not None
    assert pattern.category == PatternCategory.SPACESHIP
    assert pattern.period is not None

    run_pattern_for_period(
        pattern.cells,
        period=pattern.period,
        expected_cells=len(pattern.cells),
        check_translation=True,
    )
