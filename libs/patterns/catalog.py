"""Pattern catalog for the Game of Life."""

from dataclasses import dataclass
from enum import Enum, auto

from typeguard import typechecked

from libs.patterns.rle import parse_rle


class PatternCategory(Enum):
    """Categories of Game of Life patterns."""

    STILL_LIFE = auto()
    OSCILLATOR = auto()
    SPACESHIP = auto()


@typechecked
@dataclass(frozen=True)
class Pattern:
    """A known Game of Life pattern."""

    name: str
    category: PatternCategory
    period: int | None
    cells: frozenset[tuple[int, int]]

    @property
    def bounding_box(self) -> tuple[int, int, int, int]:
        """Return (min_r, max_r, min_c, max_c) for the pattern's cells."""
        if not self.cells:
            return 0, 0, 0, 0
        min_r = min(r for r, c in self.cells)
        max_r = max(r for r, c in self.cells)
        min_c = min(c for r, c in self.cells)
        max_c = max(c for r, c in self.cells)
        return min_r, max_r, min_c, max_c


def _parse_ascii_grid(grid_str: str) -> frozenset[tuple[int, int]]:
    """Helper to parse an ASCII grid (X=alive, .=dead)."""
    cells = set()
    for r, row in enumerate(grid_str.strip().splitlines()):
        for c, char in enumerate(row.strip()):
            if char == "X":
                cells.add((r, c))
    return frozenset(cells)


# Pulsar ASCII definition (13x13)
_PULSAR_ASCII = """
..XXX...XXX..
.............
X....X.X....X
X....X.X....X
X....X.X....X
..XXX...XXX..
.............
..XXX...XXX..
X....X.X....X
X....X.X....X
X....X.X....X
.............
..XXX...XXX..
"""

# Pentadecathlon ASCII definition (10x3)
_PENTADECATHLON_ASCII = """
..X....X..
XX.XXXX.XX
..X....X..
"""

CATALOG: list[Pattern] = [
    # Still lifes
    Pattern("Block", PatternCategory.STILL_LIFE, None, parse_rle("2o$2o!")),
    Pattern("Beehive", PatternCategory.STILL_LIFE, None, parse_rle("b2ob$o2bo$b2ob!")),
    Pattern("Loaf", PatternCategory.STILL_LIFE, None, parse_rle("b2ob$o2bo$bobo$2bo!")),
    Pattern("Boat", PatternCategory.STILL_LIFE, None, parse_rle("2ob$obo$bo!")),
    Pattern("Tub", PatternCategory.STILL_LIFE, None, parse_rle("bob$obo$bob!")),
    # Oscillators
    Pattern("Blinker", PatternCategory.OSCILLATOR, 2, parse_rle("3o!")),
    Pattern("Toad", PatternCategory.OSCILLATOR, 2, parse_rle("b3o$3ob!")),
    Pattern("Beacon", PatternCategory.OSCILLATOR, 2, parse_rle("2o$2o$2b2o$2b2o!")),
    Pattern("Pulsar", PatternCategory.OSCILLATOR, 3, _parse_ascii_grid(_PULSAR_ASCII)),
    Pattern(
        "Pentadecathlon", PatternCategory.OSCILLATOR, 15, _parse_ascii_grid(_PENTADECATHLON_ASCII)
    ),
    # Spaceships
    Pattern("Glider", PatternCategory.SPACESHIP, 4, parse_rle("bob$2bo$3o!")),
    Pattern("LWSS", PatternCategory.SPACESHIP, 4, parse_rle("o2bo$4bo$o3bo$b4o!")),
    Pattern("MWSS", PatternCategory.SPACESHIP, 4, parse_rle("2bo2b$o3bob$5bo$o4bo$b5o!")),
    Pattern("HWSS", PatternCategory.SPACESHIP, 4, parse_rle("2b2o2b$o4bob$6bo$o5bo$b6o!")),
]
