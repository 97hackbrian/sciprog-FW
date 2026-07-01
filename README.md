# Conway's Game of Life

This is a comprehensive, modular Python implementation of John Conway's "Game of Life", demonstrating efficient scientific computing techniques.

## Features

- **Efficient Core Engine**: Uses `scipy.ndimage.convolve` for fast neighbor counting.
- **Adaptive Multiprocessing**: Automatically switches to shared-memory multiprocessing for large grids, eliminating the overhead of process creation and array pickling.
- **Real-time GUI**: Built with Dear PyGui for GPU-accelerated immediate mode rendering.
- **Pattern Detection**: Detects and logs known patterns (Gliders, Oscillators, Still Lifes) using connected component analysis.
- **Data Persistence**: Saves execution statistics to a local SQLite database using SQLAlchemy 2.0.

## Installation

Ensure you have `conda` installed. Create and activate the environment:

```bash
conda env create -f environment.yml
conda activate game-of-life
```

## Usage

Generate an initial state (or use the included `initial.pkl`):
```bash
python scripts/generate_initial_state.py --pattern random --density 0.3 --rows 50 --cols 50 --out initial.pkl
```

Run the GUI simulation:
```bash
python -m game_of_life.cli --initial initial.pkl
```

Run headlessly (e.g. for CI or data collection):
```bash
python -m game_of_life.cli --initial initial.pkl --headless
```

## Architecture

- `core/`: The simulation engine (`Grid`, `Rules`, `SimulationEngine`). Headless and fully testable.
- `parallel/`: The shared-memory multiprocessing logic and adaptive dispatcher.
- `patterns/`: RLE parser, catalog of known patterns, stability tracker, and pattern detector.
- `persistence/`: SQLite database models and initial state loading logic.
- `gui/`: Dear PyGui application and views.

## Running Tests

To run the unit tests, use `pytest`:
```bash
pytest tests/
```

To run the linter and formatter:
```bash
ruff check src/ tests/
ruff format --check src/ tests/
```
