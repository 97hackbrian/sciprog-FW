#  Copyright (c) 2026. Programacion Cientifica, DISC, Antofagasta, Chile.
import logging
import multiprocessing
import os
from pathlib import Path

from numba.core.decorators import njit
from tqdm import tqdm

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


def count_primes_in_range(the_range: tuple[int, int]) -> int:
    primes = 0
    start, end = the_range
    for i in range(start, end):
        if is_prime(i):
            primes += 1
    return primes


def main() -> None:
    n = 50 * 1000 * 1000
    log.debug(f"Counting primes from 1 to {n:,} ..")

    # serial
    primes = 0
    with benchmark("serial", log):
        for i in tqdm(range(n), ncols=250, desc="counting primes (serial)"):
            if is_prime(i):
                primes += 1
    log.debug(f"primes: {primes:,} (serial)")

    # retrieve the number of cores
    num_cores = os.cpu_count() or 1
    log.debug(f"num_cores: {num_cores}.")

    # the number of work to do
    num_chunks = num_cores * 10

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

    # the pool of workers
    with benchmark("multiprocessing", log):
        with multiprocessing.Pool(num_cores) as pool:
            result = list(tqdm(
                pool.imap(count_primes_in_range, ranges),
                total=len(ranges),
                ncols=250,
                desc="count primes (multiprocessing)",
            ))
        primes = sum(result)
        log.debug(f"primes: {primes:,} (mp)")


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
