"""Configuration for the Game of Life simulation."""

import logging
import os
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path

import yaml  # type: ignore[import-untyped]
from typeguard import typechecked


class BoundaryMode(Enum):
    """Boundary conditions for the grid."""

    TOROIDAL = auto()  # Edges wrap around
    BOUNDED = auto()  # Edges are dead zones


class ComputeBackend(Enum):
    """Compute backend for the simulation."""

    AUTO = auto()
    CPU = auto()
    GPU = auto()
    NUMBA = auto()


@typechecked
@dataclass
class SimulationConfig:
    """Configuration settings for the simulation."""

    boundary_mode: BoundaryMode = BoundaryMode.TOROIDAL
    backend: ComputeBackend = ComputeBackend.AUTO
    target_generations_per_second: float = 10.0
    max_fps_limit: float = 100.0
    multiprocessing_threshold_cells: int = 10000
    all_cores: bool = False
    n_workers: int = field(default_factory=lambda: max(1, os.cpu_count() or 1 - 1))
    enable_extended_pattern_catalog: bool = True
    pattern_detection_interval: int = 1
    db_path: Path = field(default_factory=lambda: Path("data/gol.sqlite"))
    log_level: int = logging.INFO
    gui_window_width: int = 1700
    gui_window_height: int = 1150
    gui_panel_width: int = 450
    gui_plot_height: int = 250
    gui_plot_max_history: int = 200
    gui_font_scale: float = 1.3
    gui_pattern_log_max_items: int = 50
    gui_pattern_log_visible_items: int = 8
    db_batch_size: int = 25

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

        if "backend" in data:
            if isinstance(data["backend"], str):
                data["backend"] = ComputeBackend[data["backend"].upper()]

        # Convert db_path string to Path if present
        if "db_path" in data:
            data["db_path"] = Path(data["db_path"])

        return cls(**data)
