"""Logging configuration for the Game of Life project.

Adapted from the department's own reference pattern
(github.com/97hackbrian/sciprog-FW, branch `finalwork`, libs/logger.py),
extended with a rotating file handler.
"""

from __future__ import annotations

import logging
import logging.handlers
from pathlib import Path

import coloredlogs
from typeguard import typechecked

_LOG_FORMAT = (
    "%(asctime)s [%(levelname)8s] %(name)s:%(lineno)d "
    "(%(process)d/%(threadName)s) - %(message)s"
)


@typechecked
def configure_logging(level: int = logging.INFO, log_dir: Path | None = None) -> None:
    """Configure colored console logging and, optionally, a rotating file handler.

    The ``(%(process)d/%(threadName)s)`` field is intentional: this project
    uses multiprocessing for large-grid generations, and distinct PIDs in
    the log output are the cheapest way to visually confirm that worker
    processes are actually doing the work in parallel.
    """
    coloredlogs.install(
        level=level,
        fmt=_LOG_FORMAT,
        level_styles={
            "DEBUG": {"color": "black", "bright": True},
            "INFO": {"color": "green"},
            "WARNING": {"color": "magenta"},
            "ERROR": {"color": "red"},
            "CRITICAL": {"color": "red", "bold": True},
        },
        field_styles={
            "asctime": {"color": "yellow"},
            "levelname": {"bold": True},
            "name": {"color": "blue", "bold": True},
            "lineno": {"color": "magenta"},
            "process": {"color": "blue", "bold": True},
            "threadName": {"color": "cyan"},
        },
        milliseconds=True,
    )

    if log_dir is not None:
        log_dir.mkdir(parents=True, exist_ok=True)
        file_handler = logging.handlers.RotatingFileHandler(
            log_dir / "gol.log", maxBytes=2_000_000, backupCount=3, encoding="utf-8"
        )
        file_handler.setFormatter(logging.Formatter(_LOG_FORMAT))
        file_handler.setLevel(level)
        logging.getLogger().addHandler(file_handler)

    # Quiet noisy third-party loggers relevant to this project's stack.
    for noisy in ("matplotlib", "PIL", "asyncio"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
