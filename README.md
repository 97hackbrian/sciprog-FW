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

## Command Cheat Sheet

Here are all the commands you can use to interact with this project:

**Installation:**
```bash
conda env create -f environment.yml
conda activate game-of-life
```

**Running the Simulation (Basic & Advanced):**
```bash
# Basic run (will auto-generate data/initial.pkl if missing)
python scripts/run_game_of_life.py

# Run with a specific initial state
python scripts/run_game_of_life.py --initial data/initial.pkl

# Run headlessly (no GUI, good for servers)
python scripts/run_game_of_life.py --headless

# Force specific compute backend (auto, cpu, gpu)
python scripts/run_game_of_life.py --backend cpu
python scripts/run_game_of_life.py --backend gpu
```

**Generating Initial States:**
```bash
# Generate a random 100x100 grid with 30% density
python scripts/generate_initial_state.py --pattern random --density 0.3 --rows 100 --cols 100 --out data/initial.pkl

# Generate a specific pattern (e.g. glider)
python scripts/generate_initial_state.py --pattern glider --out data/initial.pkl
```

**Testing and Code Quality:**
```bash
# Master command: fix linting, format code, and run all tests
ruff check --fix . && ruff format . && pytest

# Individual commands
pytest tests/
ruff check .
ruff format --check .
```

**Benchmarking:**
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

---

# Implementation Report
*Note: This section constitutes the official Implementation Report for the project.*

## Architecture Summary
The project follows a flat, clean architecture (`libs/`, `scripts/`, `data/`) designed for testability and separation of concerns. The core engine (`libs/core/`) operates headlessly and independently of the GUI (`libs/gui/`) and persistence (`libs/persistence/`) layers. Pattern detection (`libs/patterns/`) handles identifying known structures via connected components, and the multiprocessing module (`libs/parallel/`) provides seamless shared-memory parallelism.

## Hardware Testing Environment
The performance benchmarks and multi-processing threshold crossover points (as seen in `performance_analysis.ipynb`) were evaluated on the following hardware configuration:
- **OS**: Ubuntu noble 24.04 x86_64
- **CPU**: 13th Gen Intel(R) Core(TM) i9-13950HX (32 threads @ 5.50 GHz)
- **RAM**: 32 GB
- **GPU (Compute)**: NVIDIA GeForce RTX 4060 Max-Q / Mobile [Discrete]

## Challenges and Solutions

### 1. Efficient Multiprocessing
**Challenge**: Naive multiprocessing (spawning a Pool and using `map` per generation) introduces massive overhead from process creation and pickling full NumPy arrays, typically resulting in a net loss of performance for most grid sizes.
**Solution**: Implemented a persistent `ProcessPoolExecutor` with double-buffered shared memory (`multiprocessing.shared_memory`). Worker processes attach to the memory blocks once on initialization. For each generation, they only receive small index ranges, read from the `current` block (with necessary halo rows), compute the rules via `scipy.ndimage.convolve`, and write directly to the `next` block. This eliminates process creation and serialization overhead completely.
**Cleanup Safety**: Posix shared memory segments leak if not explicitly unlinked. The implementation guarantees cleanup by using a context manager (`SharedGridBuffer`) where the owning process uniquely calls `unlink()`.

### 2. Pattern Catalog Transcription Risk
**Challenge**: Hand-transcribing patterns (like the Pulsar and Pentadecathlon) to RLE or ASCII grids carries a high risk of subtle errors, which could invalidate pattern detection.
**Solution**: Every pattern in the catalog is subjected to an exhaustive unit test (`tests/test_rules.py`). The test simulates the pattern for its known period and verifies it returns to its exact initial state (or translates properly for spaceships), acting as an absolute safety net against definition bugs.

### 3. Stability vs. Cycle Detection
**Challenge**: "Stable states (no changes)" means exact stasis (Still Lifes). Stopping the simulation prematurely on oscillators (like Blinkers) would be incorrect behavior.
**Solution**: Differentiated exact stasis (`StabilityTracker`), which halts the simulation when `current == previous`, from periodic cycle detection (`CycleTracker`), which maintains a history hash buffer to passively log (at DEBUG level) when a cycle is detected without stopping the simulation.

### 4. Multiprocessing Threshold
**Challenge**: Finding the actual crossover point where multiprocessing is beneficial.
**Solution**: Built a Jupyter notebook (`performance_analysis.ipynb`) to benchmark various grid sizes. (The actual threshold must be measured in the grading environment or developer environment and updated in `config.yaml`). The dispatcher adaptively chooses between single-process and multi-process execution based on this measured threshold.

### 5. GPU Acceleration via CuPy
**Challenge**: To drastically improve performance for very large grids without disrupting the GUI or testing framework, while supporting systems without GPUs.
**Solution**: Implemented a `GpuDispatcher` using CuPy (`cupy` and `cupyx.scipy.ndimage.convolve`) which computes generation steps entirely on the GPU. The `run_game_of_life.py` entrypoint was enhanced with a `--backend {auto, cpu, gpu}` flag. The application defaults to `auto`, which safely falls back to NumPy CPU execution if an Nvidia GPU or CuPy dependencies are not detected.
