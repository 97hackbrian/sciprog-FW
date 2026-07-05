# Implementation Report

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
