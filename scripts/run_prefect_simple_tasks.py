#  Copyright (c) 2026. Programacion Cientifica, DISC, Antofagasta, Chile.
import logging
from pathlib import Path

from prefect import task, get_run_logger, flow

from benchmarking import benchmark
from logger import configure_logging


@task
def add(x: int, y: int) -> int:
    log = get_run_logger()
    log.debug(f"add -> x: {x}, y: {y}")

    return x + y


@task
def multiply(x: int, y: int) -> int:
    log = get_run_logger()
    log.debug(f"multiply -> x: {x}, y: {y}")
    return x * y


@flow
def add_multiply(a: int, b: int) -> None:
    log = get_run_logger()
    c = add(a, b)
    log.debug(f"add({a}, {b}) = {a} + {b} = {c}")

    d = multiply(a, b)
    log.debug(f"multiply({a}, {b}) = {a} * {b} = {d}")


def main() -> None:
    a = 10
    b = 20
    add_multiply(a, b)


# call the main function
if __name__ == '__main__':
    # configure the logging
    configure_logging(logging.DEBUG)
    # get the main logger
    log = logging.getLogger(__name__)

    # get the root directory
    root_dir = Path(__file__).resolve().parent.parent
    log.debug(f"root_dir: {root_dir}")

    # get the output directory
    output_dir = root_dir / "output"
    log.debug(f"output_dir: {output_dir}")

    # measure time
    with benchmark("main", log):
        log.info("️🏎️ starting ..")
        main()
        log.info("️🏁 done.")
