# Conway's Game of Life

This is a comprehensive, modular Python implementation of John Conway's "Game of Life", demonstrating efficient scientific computing techniques.

## Features

- **Efficient Core Engine**: Uses `scipy.ndimage.convolve` for fast neighbor counting.
- **Adaptive Backend**: Automatically runs on GPU (`cupy`) if Nvidia hardware is available, or gracefully falls back to CPU (`numpy`).
- **Adaptive Multiprocessing**: Automatically switches to shared-memory multiprocessing for large grids on the CPU, eliminating the overhead of process creation and array pickling.
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

### 1. Generating an Initial State
You can generate a random starting grid or start with a specific known pattern (e.g. `glider`, `pulsar`).
```bash
# Random grid of 100x100 with 30% cell density
python scripts/generate_initial_state.py --pattern random --density 0.3 --rows 100 --cols 100 --out data/initial.pkl

# Specific pattern (e.g., a Glider)
python scripts/generate_initial_state.py --pattern glider --rows 50 --cols 50 --out data/initial.pkl
```

### 2. Running the Simulation (GUI)
The simulation supports an adaptive backend. By default, it will automatically detect and use Nvidia GPU acceleration via CuPy if available, otherwise it falls back to CPU (NumPy).

```bash
# Run with automatic backend detection (Recommended)
python scripts/run_game_of_life.py --initial data/initial.pkl --backend auto

# Force execution on CPU (Adaptive Single/Multi-process)
python scripts/run_game_of_life.py --initial data/initial.pkl --backend cpu

# Force execution on GPU (CuPy)
python scripts/run_game_of_life.py --initial data/initial.pkl --backend gpu
```

### 3. Running Headlessly (No GUI)
For CI, server execution, or data collection to SQLite, you can run the simulation headlessly. This will still respect the `--backend` flag.
```bash
# Headless CPU
python scripts/run_game_of_life.py --initial data/initial.pkl --headless --backend cpu

# Headless GPU
python scripts/run_game_of_life.py --initial data/initial.pkl --headless --backend gpu
```

### 4. Running Benchmarks
To run the performance analysis comparing CPU (Single/Multi) vs GPU execution:
```bash
jupyter nbconvert --to notebook --execute notebooks/performance_analysis.ipynb --inplace
```

## Architecture

- `libs/core/`: The simulation engine (`Grid`, `Rules`, `SimulationEngine`). Headless and fully testable.
- `libs/parallel/`: The shared-memory multiprocessing logic and adaptive dispatcher.
- `libs/patterns/`: RLE parser, catalog of known patterns, stability tracker, and pattern detector.
- `libs/persistence/`: SQLite database models and initial state loading logic.
- `libs/gui/`: Dear PyGui application and views.
- `scripts/`: Entrypoints for running the simulation and generating initial states.
- `data/`: SQLite databases and pickle files for saving/loading data.

## Running Tests and Linting

To automatically fix formatting, check code styles, and run the entire test suite in a single pass, run:
```bash
ruff check --fix . && ruff format . && pytest
```

Alternatively, you can run them individually:
```bash
pytest tests/              # Run just the tests
ruff check .               # Run the linter
ruff format --check .      # Run the formatter (dry-run)
```
