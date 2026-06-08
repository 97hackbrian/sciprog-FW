#  Copyright (c) 2026. Programacion Cientifica, DISC, Antofagasta, Chile.
import logging
from pathlib import Path

from benchmarking import benchmark  # ty:ignore[unresolved-import]
from logger import configure_logging  # ty:ignore[unresolved-import]


def main():
    pass


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
