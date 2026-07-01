# Project context — Conway's Game of Life

Living memory for this project. Read this file at the start of every
session, before touching code. Append a dated entry to the changelog after
every meaningful milestone — do not silently overwrite earlier entries.

Companion files: `ANTIGRAVITY_PROMPT.md` (the spec-of-record — what to
build) in this same directory; `rulesgameoflifeproject.md` (standing
constraints) at `.agents/rules/`; `workflowsgameoflifeproject.md` (reusable
step-by-step procedures) at `.agents/workflows/`.

---

## 1. Identity

- **What:** Conway's Game of Life, graduate scientific-computing course
  deliverable (Programación Científica con Python, UCN, Antofagasta, Chile).
- **Owner:** the human running Antigravity on this repo.
- **Grading target:** Excellent (8–10) on every rubric criterion, including
  all three bonus items (Scipy usage, Jupyter performance notebook, detecting
  more than just gliders).
- **Repo root == working directory** == the directory this file lives in.

## 2. Current status

`Phase: 0 — not yet scaffolded.` This file was authored during the planning
session, before any code exists. Update the line above as work progresses,
e.g. `Phase: 2 — core engine implemented and tested, starting persistence
layer.` Suggested phases: 0 scaffold → 1 core engine + tests → 2 persistence
→ 3 pattern detection → 4 GUI → 5 benchmark notebook + threshold tuning →
6 docs/report → 7 polish/final checklist pass.

## 3. Key architecture decisions (append, don't rewrite)

### 2026-06-30 — initial planning session

- **GUI framework: Dear PyGui**, not PySide6/Qt or Flet. Chosen for
  purpose-built heatmap plotting (`add_heat_series` maps directly onto a
  cellular-automaton grid), GPU-accelerated redraw, zero runtime network
  dependency (unlike Flet, which needs the Flutter engine at runtime — a real
  risk for a deliverable graded on a possibly-offline machine), and because
  it's less commonly seen in this kind of coursework. Full rationale in
  `ANTIGRAVITY_PROMPT.md` §7. **Fallback if it proves unworkable in the
  actual grading environment (e.g. headless, no display): PySide6 +
  QGraphicsView — ask the human before switching, don't switch silently.**
- **Fixed-size grid, not dynamically expanding.** The department's own
  reference implementation (see below) grows/shrinks the board to fit live
  cells. We deliberately do NOT do this: a fixed shape is required for
  shared-memory multiprocessing, stable pattern-detection coordinates, and a
  predictable GUI heatmap size.
- **Grid boundary mode is configurable** (toroidal default, bounded
  available via config) rather than picking one, because the PDF doesn't
  specify edge behavior and both are legitimate, testable interpretations.
- **`initial.pkl` assumed to be a raw 2D NumPy array** (shape = grid
  dimensions), with a defensive fallback for a dict-wrapped payload. The PDF
  doesn't state the exact payload shape; this is the standard convention and
  the loader is written to fail with a clear error rather than silently
  misbehave if the assumption is wrong.
- **Multiprocessing uses a persistent `ProcessPoolExecutor` + shared memory
  (double-buffered, row-block chunking with halo rows)**, not
  `Pool.map()` respawned every generation. Naive per-generation pooling is
  usually a net *slowdown* for this problem — see `ANTIGRAVITY_PROMPT.md`
  §5.2 for the full reasoning. Single-process vs. multiprocess is chosen
  **adaptively** by a `multiprocessing_threshold_cells` config value, which
  starts as a placeholder and **must be replaced** with the value measured
  in `notebooks/performance_analysis.ipynb` (bonus deliverable) — update this
  file with the final number once measured.
- **Stability stop condition is exact-match only** (grid identical to the
  immediately previous generation). A separate, non-stopping cycle-length
  diagnostic exists for logging oscillator periods, but it must never halt
  the simulation — only true stasis does. This distinction is easy to get
  wrong; a regression test guards it (`tests/test_stability.py`).
- **Pattern catalog covers all 14 named patterns** from the PDF (not just
  gliders), to satisfy the "detect more than one pattern" bonus. RLE/grid
  definitions were hand-transcribed from well-known canonical sources and
  cross-checked against documented live-cell counts, but are **not**
  pixel-verified against the PDF's own page-10 image — `tests/test_
  patterns.py` is the real safety net; if a test fails, fix the pattern
  definition, not the test.
- **Reference repo inspected:** `github.com/97hackbrian/sciprog-FW`, branch
  `finalwork` — used *only* as inspiration, not copied wholesale. Two things
  deliberately reused (adapted, with attribution, in
  `ANTIGRAVITY_PROMPT.md` §12):
  - Its `libs/logger.py` — a `coloredlogs` console logger whose format
    string includes `%(process)d/%(threadName)s`, genuinely useful here
    because it lets you visually confirm multiprocessing workers are
    actually running in parallel.
  - Its `libs/benchmarking.py` — a `perf_counter_ns()` + `humanize`-based
    timing context manager.
  Everything else in that repo (flat `sys.path`-based script layout,
  dynamically resizing board, unrelated Titanic/Iris/Prophet/spaCy scripts)
  was intentionally **not** reused.
- **Dependency versions verified live** against PyPI's JSON API and
  cross-checked against the reference repo's own `requirements.txt` on this
  date. Full pinned list in `ANTIGRAVITY_PROMPT.md` §8. `python=3.13.14`
  confirmed to have full `dearpygui` wheel support (cp313). Re-verify at
  actual setup time — these will drift.

<!-- Add new dated entries below this line as the project progresses. -->

## 4. Glossary

- **Toroidal boundary:** grid edges wrap around (right edge's neighbor is
  the left edge). **Bounded boundary:** cells beyond the grid edge count as
  permanently dead.
- **Halo row:** the one extra row above/below a multiprocessing worker's
  assigned row-block, needed to correctly count neighbors at the block's own
  edges.
- **Still life / oscillator / spaceship:** a pattern that never changes /
  that cycles through a fixed set of states with a period / that translates
  across the grid while cycling, respectively. See the pattern table in
  `ANTIGRAVITY_PROMPT.md` §4.3.
- **`@typechecked`:** the runtime type-checking decorator from the
  `typeguard` package — this is what the PDF means by "type annotations
  with `@typechecked`," not static analysis (though `mypy` is included as
  optional extra rigor).

## 5. Open items / things to verify before calling this done

- [ ] Replace the `multiprocessing_threshold_cells` placeholder with the
      value measured in the benchmark notebook; record it here once known.
- [ ] Confirm all 14 pattern-catalog entries pass their period/cell-count
      tests (§10.2 of the prompt) — flag here if any needed correction, and
      what the corrected definition turned out to be.
- [ ] Confirm Dear PyGui actually renders correctly in the environment this
      will be graded in; note here if the PySide6 fallback had to be used.
- [ ] Confirm exact conda-forge availability for the packages currently
      listed under `pip:` in `environment.yml` (not verified — see
      `ANTIGRAVITY_PROMPT.md` §8) and move any that have exact-version
      conda-forge builds into the conda `dependencies:` list.
- [ ] Remind the human to manually invite `mika.cl@gmail.com` as a
      collaborator on the private GitHub repo — the agent should not
      attempt this itself (requires the human's own credentials).

## 6. Quick links

- Course PDF requirements: fully transcribed in `ANTIGRAVITY_PROMPT.md` §1.
- Rubric + checklist mapping: `ANTIGRAVITY_PROMPT.md` §13.
- Standing rules: `.agents/rules/rulesgameoflifeproject.md`.
- Reusable workflows: `.agents/workflows/workflowsgameoflifeproject.md`.
