"""Tests for pattern detection and parsing."""

import numpy as np

from libs.patterns.catalog import CATALOG
from libs.patterns.detector import PatternDetector
from libs.patterns.rle import parse_rle


def test_rle_parsing() -> None:
    """Test standard Game-of-Life RLE string parsing."""
    # Block
    block_cells = parse_rle("2o$2o!")
    assert block_cells == frozenset([(0, 0), (0, 1), (1, 0), (1, 1)])

    # Blinker
    blinker_cells = parse_rle("3o!")
    assert blinker_cells == frozenset([(0, 0), (0, 1), (0, 2)])


def test_catalog_live_cell_counts() -> None:
    """Verify hand-transcribed patterns against documented live-cell counts.

    This acts as a safety net against transcription errors.
    """
    expected_counts = {
        "Block": 4,
        "Beehive": 6,
        "Loaf": 7,
        "Boat": 5,
        "Tub": 4,
        "Blinker": 3,
        "Toad": 6,
        "Beacon": 8,
        "Pulsar": 48,
        "Pentadecathlon": 12,
        "Glider": 5,
        "LWSS": 9,
        "MWSS": 11,
        "HWSS": 13,
    }

    for pattern in CATALOG:
        assert len(pattern.cells) == expected_counts[pattern.name], (
            f"Pattern '{pattern.name}' has {len(pattern.cells)} cells, "
            f"expected {expected_counts[pattern.name]}"
        )


def test_detector_glider_orientations() -> None:
    """Detector correctly identifies a lone glider in multiple orientations."""
    detector = PatternDetector()

    # 1. Base Glider
    grid = np.zeros((10, 10), dtype=np.uint8)
    glider = parse_rle("bob$2bo$3o!")
    for r, c in glider:
        grid[r + 1, c + 1] = 1

    matches = detector.detect(grid)
    assert len(matches) == 1
    assert matches[0].name == "Glider"
    assert matches[0].top_left_r == 1
    assert matches[0].top_left_c == 1

    # 2. Rotated 90 degrees
    grid2 = np.rot90(grid)
    matches2 = detector.detect(grid2)
    assert len(matches2) == 1
    assert matches2[0].name == "Glider"

    # 3. Mirrored
    grid3 = np.fliplr(grid)
    matches3 = detector.detect(grid3)
    assert len(matches3) == 1
    assert matches3[0].name == "Glider"
