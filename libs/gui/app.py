"""Main GUI application."""

import time
from typing import Any

import dearpygui.dearpygui as dpg  # type: ignore[import-untyped]

from libs.config import BoundaryMode, SimulationConfig
from libs.core.engine import SimulationEngine
from libs.gui.controls import Controls
from libs.gui.views import GridView, StatsView


class GameOfLifeApp:
    """Dear PyGui application for Game of Life."""

    def __init__(
        self, engine: SimulationEngine, config: SimulationConfig, initial_state: Any
    ) -> None:
        self.engine = engine
        self.config = config
        self.initial_state = initial_state

        self.is_playing = True
        self.target_fps = config.target_generations_per_second
        self.last_update_time = time.time()

        dpg.create_context()
        self._setup_window()
        dpg.create_viewport(title="Conway's Game of Life", width=1200, height=800)
        dpg.setup_dearpygui()

    def _setup_window(self) -> None:
        with dpg.window(tag="Primary Window"):
            with dpg.group(horizontal=True):
                # Left panel: controls and stats
                with dpg.child_window(width=300, tag="LeftPanel"):
                    self.controls = Controls(
                        parent="LeftPanel",
                        on_play_pause=self.toggle_play,
                        on_step=self.step_once,
                        on_reset=self.reset_sim,
                        on_speed_change=self.set_speed,
                        on_boundary_change=self.set_boundary,
                    )

                    dpg.add_separator(parent="LeftPanel")
                    self.stats_view = StatsView(parent="LeftPanel")

                    # Set the backend label
                    from libs.parallel.dispatch import GpuDispatcher, MultiprocessDispatcher

                    if isinstance(self.engine.dispatcher, GpuDispatcher):
                        try:
                            import cupy as cp  # type: ignore

                            props = cp.cuda.runtime.getDeviceProperties(0)
                            model = props["name"].decode("utf-8")
                            self.stats_view.set_backend(f"GPU ({model})")
                        except Exception:
                            self.stats_view.set_backend("GPU (Unknown)")
                    elif isinstance(self.engine.dispatcher, MultiprocessDispatcher):
                        self.stats_view.set_backend(f"CPU (Multi, {self.config.n_workers} workers)")
                    else:
                        self.stats_view.set_backend("CPU (Single Process)")

                # Right panel: grid
                with dpg.child_window():
                    rows, cols = self.initial_state.shape
                    self.grid_view = GridView(parent=dpg.last_item(), rows=rows, cols=cols)

        # Draw initial state
        self.grid_view.update(self.engine.grid.array)

    def toggle_play(self) -> bool:
        """Toggle the playing state of the simulation."""
        self.is_playing = not self.is_playing
        return self.is_playing

    def step_once(self) -> None:
        """Perform a single step of the simulation and pause."""
        self.is_playing = False
        self.controls.force_pause()
        self._do_step()

    def reset_sim(self) -> None:
        """Reset the simulation to its initial state."""
        self.engine.reset(self.initial_state)
        self.stats_view.reset()
        self.controls.clear_patterns()
        self.grid_view.update(self.engine.grid.array)

    def set_speed(self, speed: float) -> None:
        """Set the target frames per second."""
        self.target_fps = speed

    def set_boundary(self, mode: BoundaryMode) -> None:
        """Change the boundary mode and reset the simulation."""
        self.config.boundary_mode = mode
        self.engine.config.boundary_mode = mode
        self.reset_sim()

    def _do_step(self) -> None:
        result = self.engine.step()
        self.grid_view.update(self.engine.grid.array)
        self.stats_view.update(
            result.iteration,
            result.live_cells,
            result.dead_cells,
            result.execution_time_ms,
            result.is_stable,
        )
        self.controls.add_patterns(result.iteration, result.detected_patterns)

        if result.is_stable and self.is_playing:
            self.is_playing = False
            self.controls.force_pause()

    def run(self) -> None:
        """Run the main GUI loop."""
        dpg.show_viewport()
        dpg.set_primary_window("Primary Window", True)

        while dpg.is_dearpygui_running():
            current_time = time.time()
            if self.is_playing and (
                self.target_fps >= 1000.0
                or (current_time - self.last_update_time) >= (1.0 / self.target_fps)
            ):
                self._do_step()
                self.last_update_time = current_time

            dpg.render_dearpygui_frame()

        dpg.destroy_context()
