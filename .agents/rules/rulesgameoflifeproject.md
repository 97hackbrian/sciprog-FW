---
trigger: always_on
---

# Rules — Game of Life project (Antigravity)

> **Target location in the repo:** `.agents/rules/rulesgameoflifeproject.md`

Standing constraints for this project. They rarely change; `context.md` is
where things that *do* change (decisions, status) live.

Companion files: `ANTIGRAVITY_PROMPT.md` and `context.md` (repo root),
`workflowsgameoflifeproject.md` at `.agents/workflows/` (reusable
step-by-step procedures).

This file must live at `.agents/rules/rulesgameoflifeproject.md` from the
repo root — that's where this Antigravity project expects standing agent
rules to be picked up. Create the `.agents/rules/` directory if it doesn't
exist yet.

---

## Environment
- **conda only.** No Docker, no `Dockerfile`, no `docker-compose.yml`
  anywhere in the repository, ever.
- **Every dependency pinned to an exact version** in both `environment.yml`
  and `requirements.txt`. Never introduce `>=`, `~=`, `^`, or an unpinned
  entry. If you add a new dependency mid-project, pin it and add it to both
  files, and note why in `context.md`.
- Python 3.13.14 unless `context.md` records a documented change.

## Code style
- Format and lint with `ruff` (`ruff format`, `ruff check`). Configure once
  in `pyproject.toml`; don't hand-tune formatting.
- Full type hints on every function/method signature; `@typechecked` from
  `typeguard` on every public function, method, and `__init__`.
- Google-style docstrings on every public module, class, and function — no
  exceptions for "obvious" ones.
- **Never name a module or package `logging`, `types`, `json`, or anything
  else that shadows the Python standard library.** The project's own logging
  setup lives at `game_of_life/logging_config.py` specifically because of
  this rule.
- Two-space or four-space indentation is `ruff`'s call, not a personal
  preference — don't override the formatter's output by hand.

## Architecture boundaries
- `core/` (the simulation engine) must never import anything from `gui/`.
  The engine has to be usable headlessly (tests, the benchmark notebook,
  `--headless` CLI mode) without pulling in Dear PyGui.
- `gui/` code contains presentation logic only — no Game-of-Life rule logic,
  no direct SQLAlchemy session handling. It calls into `core/`,
  `persistence/`, and `patterns/` through their public interfaces.
- Configuration is centralized in `config.py` / `config.yaml` — no magic
  numbers scattered through the codebase (grid thresholds, worker counts,
  DB paths, etc. all come from `SimulationConfig`).
- The persistence layer is accessed only through `persistence/database.py`'s
  session helpers — no raw SQL or ad hoc `sqlite3` connections elsewhere.

## Multiprocessing safety
- Never share mutable state across processes without going through
  `multiprocessing.shared_memory` (or another explicit IPC mechanism) —
  no relying on process-fork copy-on-write semantics for correctness.
- Every `SharedMemory` block created by the owning process must be
  `unlink()`-ed by that same process on shutdown. Worker processes only ever
  `close()` their view, never `unlink()`. Wrap allocation/cleanup in a
  context manager so this can't be forgotten on an exception path.
- Build the `ProcessPoolExecutor` once and reuse it; never create a new pool
  per generation.

## Testing
- Every pattern added to the catalog gets a corresponding unit test
  asserting its documented period (or still-life stasis) and live-cell
  count. This is not optional polish — it's the actual verification
  mechanism for hand-transcribed pattern data (see `context.md` §3).
- Run the full `pytest` suite before considering any module "done." A module
  isn't finished when it runs once in a manual smoke test.
- New multiprocessing code gets a test comparing its output against the
  single-process path on the same input.

## Git
- Small, incremental commits with descriptive messages — not one commit at
  the end of the project. Commit after each module is working and tested,
  not after the whole feature area is done.
- Never commit `data/*.sqlite`, `logs/`, `__pycache__/`, or notebook
  checkpoints — confirm `.gitignore` covers these before the first commit.
- Creating the GitHub repository can be automated (`gh repo create ...`) if
  `gh` is authenticated. **Inviting `mika.cl@gmail.com` as a collaborator is
  a manual step for the human** — it requires their own GitHub permissions.
  Prepare everything up to that point, then stop and ask.

## Context maintenance
- Update `context.md` after every meaningful milestone: a new architecture
  decision, a changed default (e.g. the measured multiprocessing threshold),
  a pattern definition that needed correcting, a risk that got resolved.
  Append a dated entry — never delete or silently rewrite a previous one.
- If anything in this file, `workflowsgameoflifeproject.md`, or
  `ANTIGRAVITY_PROMPT.md` turns out to be wrong or infeasible once real code
  exists, say so explicitly in `context.md` rather than quietly deviating.