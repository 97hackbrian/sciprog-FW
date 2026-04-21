#  Copyright (c) 2026. Programacion Cientifica, DISC, Antofagasta, Chile.

import datetime
import logging
import time
from contextlib import contextmanager
from typing import Optional, Generator

import humanize
from typeguard import typechecked


@contextmanager
@typechecked
def benchmark(
        operation_name: Optional[str] = None,
        log: Optional[logging.Logger] = None,
) -> Generator[None, None, None]:
    # start time
    start: int = time.perf_counter_ns()

    try:
        yield
    finally:
        elapsed: int = time.perf_counter_ns() - start
        elapsed_microseconds = elapsed / 1_000
        delta = datetime.timedelta(microseconds=elapsed_microseconds)

        human_time = humanize.precisedelta(
            delta, minimum_unit="microseconds", format="%.2f"
        )
        if not log:
            log = logging.getLogger(__name__)

        if operation_name:
            log.debug(f"⏱️{operation_name} executed in {human_time}")
        else:
            log.debug(f"⏱️executed in {human_time}")
