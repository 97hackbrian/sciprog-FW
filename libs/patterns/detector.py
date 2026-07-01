"""Pattern detection logic."""

import logging
from dataclasses import dataclass

import numpy as np
from scipy.ndimage import find_objects, label
from typeguard import typechecked

from game_of_life.patterns.catalog import CATALOG

log = logging.getLogger(__name__)


@typechecked
@dataclass(frozen=True)
class PatternMatch:
    """A matched pattern instance."""

    name: str
    top_left_r: int
    top_left_c: int


@typechecked
class PatternDetector:
    """Detects Game of Life patterns using connected component analysis."""

    def __init__(self, enable_extended_catalog: bool = True):
        self.enable_extended = enable_extended_catalog
        # Pre-compute target patterns as sets of coordinates
        # and all their 8 transformations (4 rotations x 2 mirrors)
        self._target_patterns: dict[str, list[frozenset[tuple[int, int]]]] = {}
        for p in CATALOG:
            if not self.enable_extended and p.name != "Glider":
                continue
            self._target_patterns[p.name] = self._generate_transformations(p.cells)

    def _generate_transformations(
        self, cells: frozenset[tuple[int, int]]
    ) -> list[frozenset[tuple[int, int]]]:
        """Generate all 8 orientations of a pattern, normalized to (0,0)."""
        if not cells:
            return []

        transforms = []

        # Original points as an array
        points = np.array(list(cells))

        for mirror in (False, True):
            for rot in range(4):
                transformed = points.copy()

                # Mirror horizontally
                if mirror:
                    transformed[:, 1] = -transformed[:, 1]

                # Rotate 90 degrees rot times
                for _ in range(rot):
                    # (r, c) -> (c, -r)
                    temp = transformed[:, 0].copy()
                    transformed[:, 0] = transformed[:, 1]
                    transformed[:, 1] = -temp

                # Normalize to top-left (0,0)
                min_r = np.min(transformed[:, 0])
                min_c = np.min(transformed[:, 1])
                transformed[:, 0] -= min_r
                transformed[:, 1] -= min_c

                # Convert back to set of tuples
                t_set = frozenset((int(r), int(c)) for r, c in transformed)
                if t_set not in transforms:
                    transforms.append(t_set)

        return transforms

    def detect(self, grid: np.ndarray) -> list[PatternMatch]:
        """Find patterns in the grid and log them."""
        # 8-connectivity is required (e.g. for gliders)
        structure = np.ones((3, 3), dtype=int)
        labeled, num_features = label(grid, structure=structure)

        if num_features == 0:
            return []

        slices = find_objects(labeled)
        matches = []

        for i, sl in enumerate(slices):
            if sl is None:
                continue

            # Extract the component's bounding box
            r_slice, c_slice = sl
            top_left_r = r_slice.start
            top_left_c = c_slice.start

            # The mask of this specific component within the bounding box
            component_mask = labeled[sl] == (i + 1)

            # Convert to coordinate set relative to bounding box top-left
            component_cells = frozenset(
                (int(r), int(c))
                for r in range(component_mask.shape[0])
                for c in range(component_mask.shape[1])
                if component_mask[r, c]
            )

            # Match against known patterns
            matched_name = None
            for name, transforms in self._target_patterns.items():
                if component_cells in transforms:
                    matched_name = name
                    break

            if matched_name:
                match = PatternMatch(
                    name=matched_name, top_left_r=top_left_r, top_left_c=top_left_c
                )
                matches.append(match)

                if matched_name == "Glider":
                    log.info(f"Detected Glider at ({top_left_r}, {top_left_c})")
                elif self.enable_extended:
                    log.debug(f"Detected {matched_name} at ({top_left_r}, {top_left_c})")

        return matches
