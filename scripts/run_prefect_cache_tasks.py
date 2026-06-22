#  Copyright (c) 2026. Programacion Cientifica, DISC, Antofagasta, Chile.
import logging
import random
import time
from datetime import timedelta
from pathlib import Path

from prefect import task, get_run_logger, flow

from benchmarking import benchmark  # ty:ignore[unresolved-import]
from logger import configure_logging  # ty:ignore[unresolved-import]


@task(retries=3, retry_delay_seconds=5, log_prints=True)
def fetch_price(product_id: int) -> float:
    log = get_run_logger()
    log.debug(f"fetching price for product_id: {product_id} ..")

    # simulate a error
    if random.random() < 0.6:
        raise ValueError(f"error in fetch price for product_id {product_id}.")

    # get the price
    price = random.uniform(10, 100)
    log.debug(f"fetched price for product_id: {product_id} -> {price}.")
    return price


def static_cache_key(context, parameters):
    # return a constant
    return "this-is-a-static-cache-key"


@task(cache_key_fn=static_cache_key, cache_expiration=timedelta(seconds=60), log_prints=True)
def expensive_task() -> int:
    log = get_run_logger()
    log.debug(f"expensive_task()")
    # this line take a forever to complete
    time.sleep(10)
    return 0


@flow(log_prints=True)
def retrieve_price_value():
    log = get_run_logger()
    product_id = 12345
    log.debug(f"fetching price for product_id: {product_id} ..")
    try:
        price = fetch_price(product_id)
        log.debug(f"fetched price for product_id: {product_id} -> {price}.")
    except Exception as e:
        log.error(f"error fetching price for product_id: {product_id} -> {e}.")


def main() -> None:
    # retrieve_price_value()

    for i in range(10):
        log.debug(f"expensive task for {i} ..")
        expensive_task()
    log.debug(f"main finished")


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
