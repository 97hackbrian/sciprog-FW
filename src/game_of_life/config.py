"""Configuration for the Game of Life simulation."""

import logging
import os
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path

import yaml
from typeguard import typechecked


class BoundaryMode(Enum):
    """Boundary conditions for the grid."""
    TOROIDAL = auto()  # Edges wrap around
    BOUNDED = auto()   # Edges are dead zones


@typechecked
@dataclass
class SimulationConfig:
    """Configuration settings for the simulation."""
    boundary_mode: BoundaryMode = BoundaryMode.TOROIDAL
    target_generations_per_second: float = 10.0
    multiprocessing_threshold_cells: int = 10000
    n_workers: int = field(default_factory=lambda: max(1, os.cpu_count() or 1 - 1))
    enable_extended_pattern_catalog: bool = True
    pattern_detection_interval: int = 1
    db_path: Path = field(default_factory=lambda: Path("data/gol.sqlite"))
    log_level: int = logging.INFO

    @classmethod
    def load(cls, path: Path | None = None) -> "SimulationConfig":
        """Load configuration from a YAML file, falling back to defaults."""
        if path is None or not path.exists():
            return cls()

        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        # Convert boundary_mode string to enum if present
        if "boundary_mode" in data:
            if isinstance(data["boundary_mode"], str):
                data["boundary_mode"] = BoundaryMode[data["boundary_mode"].upper()]

        # Convert db_path string to Path if present
        if "db_path" in data:
            data["db_path"] = Path(data["db_path"])

        return cls(**data)
