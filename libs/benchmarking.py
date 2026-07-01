"""Lightweight timing utility.

Adapted from the department's own reference pattern
(github.com/97hackbrian/sciprog-FW, branch `finalwork`, libs/benchmarking.py).
"""

from __future__ import annotations

import datetime
import logging
import time
from contextlib import contextmanager
from typing import Generator

import humanize


@contextmanager
def benchmark(
    operation_name: str | None = None, log: logging.Logger | None = None
) -> Generator[None, None, None]:
    """Measure elapsed time for a code block and log a human-readable duration."""
    log = log or logging.getLogger(__name__)
    start_ns = time.perf_counter_ns()
    try:
        yield
    finally:
        elapsed_ns = time.perf_counter_ns() - start_ns
        delta = datetime.timedelta(seconds=elapsed_ns / 1_000_000_000)
        human_time = humanize.precisedelta(delta, minimum_unit="microseconds", format="%.2f")
        label = f"{operation_name} " if operation_name else ""
        log.debug(f"\u23f1\ufe0f {label}executed in {human_time}")
