#  Copyright (c) 2026. Programacion Cientifica, DISC, Antofagasta, Chile.

import logging
from pathlib import Path

from data_profiling import ProfileReport
from ucimlrepo import fetch_ucirepo

from benchmarking import benchmark  # ty:ignore[unresolved-import]
from logger import configure_logging  # ty:ignore[unresolved-import]


def main():
    # retrieve the dataset
    iris = fetch_ucirepo(id=53)

    # data (as pandas dataframes)
    X = iris.data.features
    y = iris.data.targets

    # log.info(f"Iris metadata:\n{iris.metadata}")
    # log.info(f"Iris variables:\n{iris.variables}")

    # log.info(f"head X:\n{X.head()}")
    # log.info(f"head y:\n{y.head()}")

    # assembly: X + y
    df = X.copy()
    df["class"] = y

    # head & tail
    log.debug(f"iris df:\n{df.head()}.")
    log.debug(f"iris df:\n{df.tail()}.")

    # describe
    log.debug(f"iris df describe:\n{df.describe()}.")

    profile = ProfileReport(df, title="Iris Profiling")

    profile.to_file(output_dir / "iris_profiling.html")


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
