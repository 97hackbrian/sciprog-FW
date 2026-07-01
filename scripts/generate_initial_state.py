import argparse
import pickle
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np

from libs.patterns.catalog import CATALOG
from libs.patterns.rle import parse_rle


def main() -> None:
    """Generate the initial state pickle file."""
    parser = argparse.ArgumentParser(description="Generate Game of Life initial state.")
    parser.add_argument(
        "--pattern", type=str, default="glider", help="Pattern to place, or 'random'"
    )
    parser.add_argument("--rows", type=int, default=50, help="Grid rows")
    parser.add_argument("--cols", type=int, default=50, help="Grid columns")
    parser.add_argument("--density", type=float, default=0.2, help="Density for random fill")
    parser.add_argument("--out", type=Path, default=Path("initial.pkl"), help="Output path")
    args = parser.parse_args()

    grid = np.zeros((args.rows, args.cols), dtype=np.uint8)

    if args.pattern == "random":
        grid = np.random.choice(
            [0, 1], size=(args.rows, args.cols), p=[1 - args.density, args.density]
        ).astype(np.uint8)
    else:
        # Find pattern in catalog
        pattern = next((p for p in CATALOG if p.name.lower() == args.pattern.lower()), None)
        if pattern:
            cells = pattern.cells
        else:
            print(f"Unknown pattern '{args.pattern}'. Using a glider.")
            cells = parse_rle("bob$2bo$3o!")

        # Center the pattern
        if cells:
            min_r = min(r for r, c in cells)
            max_r = max(r for r, c in cells)
            min_c = min(c for r, c in cells)
            max_c = max(c for r, c in cells)

            height = max_r - min_r + 1
            width = max_c - min_c + 1

            offset_r = (args.rows - height) // 2 - min_r
            offset_c = (args.cols - width) // 2 - min_c

            for r, c in cells:
                if 0 <= r + offset_r < args.rows and 0 <= c + offset_c < args.cols:
                    grid[r + offset_r, c + offset_c] = 1

    with open(args.out, "wb") as f:
        pickle.dump(grid, f)

    print(f"Generated {args.out} with shape {grid.shape} and {np.sum(grid)} live cells.")


if __name__ == "__main__":
    main()
