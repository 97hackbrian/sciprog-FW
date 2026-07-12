"""Main GUI application."""

import logging
import time
from typing import Any

import dearpygui.dearpygui as dpg  # type: ignore[import-untyped]

from libs.config import BoundaryMode, ComputeBackend, SimulationConfig
from libs.core.engine import SimulationEngine
from libs.gui.controls import Controls
from libs.gui.views import GridView, StatsView

log = logging.getLogger(__name__)


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

        # Pending backend switch (deferred to main thread)
        self._pending_backend: ComputeBackend | None = None
        self._pending_all_cores: bool | None = None

        dpg.create_context()
        self._setup_window()
        dpg.create_viewport(
            title="Conway's Game of Life",
            width=self.config.gui_window_width,
            height=self.config.gui_window_height,
        )
        dpg.setup_dearpygui()
        dpg.set_global_font_scale(self.config.gui_font_scale)

    def _setup_window(self) -> None:
        with dpg.window(tag="Primary Window"):
            with dpg.group(horizontal=True):
                # Left panel: controls and stats
                with dpg.child_window(width=self.config.gui_panel_width, tag="LeftPanel"):
                    self.controls = Controls(
                        parent="LeftPanel",
                        on_play_pause=self.toggle_play,
                        on_step=self.step_once,
                        on_reset=self.reset_sim,
                        on_speed_change=self.set_speed,
                        on_boundary_change=self.set_boundary,
                        on_backend_change=self._request_backend_switch,
                        on_all_cores_change=self._request_all_cores_switch,
                        max_fps=self.config.max_fps_limit,
                        max_pattern_log_items=self.config.gui_pattern_log_max_items,
                        visible_pattern_log_items=self.config.gui_pattern_log_visible_items,
                    )

                    # Initialize checkbox state
                    dpg.set_value(
                        self.controls.all_cores_checkbox,
                        getattr(self.config, "all_cores", False),
                    )

                    dpg.add_separator(parent="LeftPanel")
                    self.stats_view = StatsView(
                        parent="LeftPanel",
                        plot_height=self.config.gui_plot_height,
                        max_history=self.config.gui_plot_max_history,
                    )

                    # Set initial backend and topology labels
                    self._update_backend_label()
                    self._update_topology_label()

                # Right panel: grid
                with dpg.child_window():
                    rows, cols = self.initial_state.shape
                    self.grid_view = GridView(parent=dpg.last_item(), rows=rows, cols=cols)

        # Draw initial state
        self.grid_view.update(self.engine.grid.array)

    def _update_backend_label(self) -> None:
        """Update the stats view with the actual backend in use."""
        import cupy as cp  # type: ignore

        from libs.parallel.dispatch import GpuDispatcher, MultiprocessDispatcher, NumbaDispatcher

        is_gpu = False

        if isinstance(self.engine.dispatcher, GpuDispatcher):
            is_gpu = True
            try:
                import cupy as cp  # type: ignore

                props = cp.cuda.runtime.getDeviceProperties(0)
                model = props["name"].decode("utf-8")
                label = f"GPU ({model})"
            except Exception:
                label = "GPU (Unknown)"
        elif isinstance(self.engine.dispatcher, MultiprocessDispatcher):
            actual_workers = self.engine.dispatcher.pool.n_workers
            label = f"CPU SciPy (Multi, {actual_workers} workers)"
        elif isinstance(self.engine.dispatcher, NumbaDispatcher):
            label = "CPU Numba JIT (Multi-threaded)"
        else:
            label = "CPU SciPy (Single Process)"

        self.stats_view.set_backend(label)
        self.controls.set_backend_status(f"Active: {label}")
        self.controls.set_all_cores_enabled(not is_gpu)

    def _update_topology_label(self) -> None:
        """Update the stats view topology label."""
        from libs.parallel.dispatch import GpuDispatcher
        from libs.parallel.topology import get_topology_info

        if isinstance(self.engine.dispatcher, GpuDispatcher):
            self.stats_view.set_topology("N/A", visible=False)
            return

        p_cores, e_cores = get_topology_info()
        total = len(p_cores) + len(e_cores)
        if getattr(self.config, "all_cores", False) or not e_cores:
            active = total
            self.stats_view.set_topology(f"All Cores Active ({active}/{total})", visible=True)
        else:
            active = len(p_cores)
            self.stats_view.set_topology(f"P-Cores Active ({active}/{total})", visible=True)

    def _request_backend_switch(self, backend: ComputeBackend) -> None:
        """Request a backend switch. Deferred to main thread to avoid segfaults.

        Dear PyGui callbacks run on a background thread. Numba JIT compilation
        and multiprocessing pool creation are not safe from non-main threads.
        We store the request and process it on the main loop.
        """
        self._pending_backend = backend
        self.controls.set_backend_status("Switching...")

    def _apply_backend_switch(self) -> None:
        """Apply a pending backend switch on the main thread."""
        backend = self._pending_backend
        self._pending_backend = None

        if backend is None:
            return

        log.info(f"Switching backend to {backend.name}...")

        # Update config
        self.config.backend = backend
        self.engine.config.backend = backend

        # Reset the simulation (this shuts down old dispatcher and creates new one)
        self.reset_sim()

        # Update GUI labels
        self._update_backend_label()
        self.controls.set_backend_combo(self.config.backend)

        # Ensure it plays automatically after switch
        self.is_playing = True
        self.controls.force_play()

        log.info(f"Backend switched to {backend.name} successfully.")

    def _request_all_cores_switch(self, all_cores: bool) -> None:
        """Request a switch of CPU core affinity."""
        self._pending_all_cores = all_cores

    def _apply_all_cores_switch(self) -> None:
        """Apply the all cores switch on the main thread."""
        all_cores = self._pending_all_cores
        self._pending_all_cores = None

        if all_cores is None:
            return

        log.info(f"Switching all_cores affinity to: {all_cores}")

        self.config.all_cores = all_cores
        self.engine.config.all_cores = all_cores

        # Apply process-level affinity immediately
        from libs.parallel.topology import apply_pcore_affinity

        apply_pcore_affinity(all_cores=all_cores)

        self.reset_sim()
        self._update_topology_label()

        # Ensure it plays automatically after switch
        self.is_playing = True
        self.controls.force_play()

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
        self._update_backend_label()
        self._update_topology_label()

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
        self.grid_view.update(self.engine.grid.array, result.detected_patterns)
        self.stats_view.update(
            result.iteration,
            result.live_cells,
            result.dead_cells,
            result.execution_time_ms,
            result.is_stable,
        )
        self.controls.add_patterns(result.iteration, result.detected_patterns)

        for p in result.detected_patterns:
            if p.name == "Glider":
                # Matches the red GUI text format in the terminal
                log.info(
                    f"\033[91mGen {result.iteration}: Glider @ "
                    f"({p.top_left_r}, {p.top_left_c})\033[0m"
                )

        if result.is_stable and self.is_playing:
            self.is_playing = False
            self.controls.force_pause()

    def run(self) -> None:
        """Run the main GUI loop."""
        dpg.show_viewport()
        dpg.set_primary_window("Primary Window", True)

        while dpg.is_dearpygui_running():
            # Process pending switches on the main thread
            if self._pending_backend is not None:
                self._apply_backend_switch()
            if self._pending_all_cores is not None:
                self._apply_all_cores_switch()

            current_time = time.time()
            if self.is_playing and (
                self.target_fps >= self.config.max_fps_limit
                or (current_time - self.last_update_time) >= (1.0 / self.target_fps)
            ):
                self._do_step()
                self.last_update_time = current_time

            dpg.render_dearpygui_frame()

        dpg.destroy_context()
