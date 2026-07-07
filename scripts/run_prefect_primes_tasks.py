#  Copyright (c) 2026. Programacion Cientifica, DISC, Antofagasta, Chile.
import logging
import os
from pathlib import Path

from numba import njit
from prefect import task, flow

from benchmarking import benchmark
from logger import configure_logging


@njit(fastmath=True)
def is_prime(num: int):
    # less than 2 always false
    if num < 2:
        return False
    # if exactly 2 -> true
    if num == 2:
        return True
    # multiple of two or three -> false
    if num % 2 == 0 or num % 3 == 0:
        return False

    # try all the values
    for i in range(5, int(num ** 0.5) + 1, 6):
        if num % i == 0:
            return False

    return True


@task
def count_primes_in_range(the_range: tuple[int, int]) -> int:
    primes = 0
    start, end = the_range
    for i in range(start, end):
        if is_prime(i):
            primes += 1
    log.debug(f"primes: {primes} in range: {the_range}.")
    return primes


@task
def combine_counts(a: int, b: int) -> int:
    return a + b


@flow
def count_primes(n: int) -> int:
    # retrieve the number of cores
    num_cores = os.cpu_count() or 1
    log.debug(f"num_cores: {num_cores}.")

    # the number of work to do
    num_chunks = num_cores * 4

    # the size of each work
    chunk_size = n // num_chunks

    # divide the space in (start, end)
    ranges = []
    for i in range(num_chunks):
        start = i * chunk_size
        if i == num_chunks - 1:
            end = n
        else:
            end = (i + 1) * chunk_size
        ranges.append((start, end))
    log.debug(f"ranges size: {len(ranges)}.")

    futures = count_primes_in_range.map(ranges)

    result = [f.result() for f in futures]
    log.debug(f"result: {result}")

    # first result
    total_primes = result[0]
    for r in result[1:]:
        total_primes = combine_counts(total_primes, r)
    return total_primes


def main() -> None:
    n = 50 * 1000 * 1000
    log.debug(f"Counting primes from 1 to {n:,} ..")

    primes = count_primes(n)
    log.debug(f"primes: {primes:,} (prefect)")


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
