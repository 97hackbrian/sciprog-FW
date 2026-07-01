---
description: # Workflows — Game of Life project (Antigravity)
---

> **Target location in the repo:** `.agents/workflows/workflowsgameoflifeproject.md`

Reusable, repeatable procedures. If your Antigravity version supports
slash-command-style workflows, register each of these under the given name;
otherwise, treat each as a checklist to run manually when the situation
applies.

Companion files: `ANTIGRAVITY_PROMPT.md` and `context.md` (repo root),
`rulesgameoflifeproject.md` at `.agents/rules/` (standing constraints).

This file must live at `.agents/workflows/workflowsgameoflifeproject.md`
from the repo root — that's where this Antigravity project expects reusable
workflows to be picked up. Create the `.agents/workflows/` directory if it
doesn't exist yet.

---

## `/setup-environment`
1. `conda env create -f environment.yml` (or `conda env update` if it
   already exists).
2. `conda activate game-of-life`.
3. Sanity-check imports: `python -c "import numpy, scipy, sqlalchemy,
   dearpygui, typeguard, coloredlogs, humanize, yaml"`.
4. If any package under `pip:` in `environment.yml` fails to resolve, check
   `conda search -c conda-forge <name>=<version>` before falling back to a
   different pin — and record the outcome in `context.md`.

## `/run-tests`
1. `pytest tests/ -v`.
2. If any pattern test in `test_patterns.py` fails, treat it as a
   pattern-definition bug (fix `patterns/catalog.py`), not a test bug — see
   the standing note in `context.md` §3.
3. `ruff check .` and `ruff format --check .` — fix anything flagged before
   moving on.

## `/add-pattern`
Use when adding a pattern to the catalog beyond the 14 already specified.
1. Find or derive the pattern's RLE/coordinate definition and its documented
   period (or "still life" if none).
2. Add it to `patterns/catalog.py`.
3. Add a unit test in `tests/test_patterns.py` asserting the documented
   period/cell count, following the existing pattern-test structure.
4. Run `/run-tests`. Only consider the pattern added once its test passes.
5. Update the pattern table in `context.md` if it's a permanent addition.

## `/benchmark`
1. Open `notebooks/performance_analysis.ipynb`.
2. Run all cells — this benchmarks grid sizes × single-process/multiprocess
   strategies and produces the grid-size-vs-runtime plot.
3. Save the notebook with outputs included (a grader should see the plot
   without re-running).
4. Read off the crossover point where multiprocessing starts winning; update
   `multiprocessing_threshold_cells` in `config.py`/`config.yaml` to that
   value.
5. Record the new value and the reasoning as a dated entry in `context.md`.

## `/prepare-commit`
1. `ruff format .` then `ruff check --fix .`.
2. `/run-tests` — do not commit on a red test suite.
3. Review the diff for stray debug prints, commented-out code, or
   accidentally-committed data/log files.
4. Stage and commit with a message describing *what* changed and, briefly,
   *why*.

## `/update-context`
1. Open `context.md`.
2. Append a new dated entry under §3 (or add to §5 "open items" if it's a
   risk/TODO rather than a decision) describing what changed and why.
3. Never delete or rewrite an existing entry — this file is a log.

## `/finalize-deliverables`
Run once the implementation is functionally complete, before declaring the
project done.
1. Walk every line of the checklist (a)–(o) and the six deliverables in
   `ANTIGRAVITY_PROMPT.md` §13 — confirm each has a concrete, checkable
   answer, not just "probably fine."
2. Confirm `environment.yml` and `requirements.txt` list the same versions.
3. Confirm `README.md` covers description, installation, and usage.
4. Write or finalize `REPORT.md` (≤3 pages): implementation summary, real
   challenges encountered (pull these from `context.md`'s decision log —
   don't invent generic ones), and the solutions applied.
5. Confirm `logs/gol.log` from a real run shows at least one glider
   detection, and `data/gol.sqlite` has populated rows.
6. Walk the §16 "Definition of done" checklist in `ANTIGRAVITY_PROMPT.md`
   top to bottom.
7. Remind the human about the manual GitHub-collaborator-invite step.