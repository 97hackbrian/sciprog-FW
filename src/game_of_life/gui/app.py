"""Main GUI application."""

import time

import dearpygui.dearpygui as dpg

from game_of_life.config import SimulationConfig, BoundaryMode
from game_of_life.core.engine import SimulationEngine
from game_of_life.gui.controls import Controls
from game_of_life.gui.views import GridView, StatsView


class GameOfLifeApp:
    """Dear PyGui application for Game of Life."""
    
    def __init__(self, engine: SimulationEngine, config: SimulationConfig, initial_state):
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
                with dpg.child_window(width=300):
                    self.controls = Controls(
                        parent=dpg.last_item(),
                        on_play_pause=self.toggle_play,
                        on_step=self.step_once,
                        on_reset=self.reset_sim,
                        on_speed_change=self.set_speed,
                        on_boundary_change=self.set_boundary
                    )
                    
                    dpg.add_separator()
                    self.stats_view = StatsView(parent=dpg.last_item())
                    
                # Right panel: grid
                with dpg.child_window():
                    rows, cols = self.initial_state.shape
                    self.grid_view = GridView(parent=dpg.last_item(), rows=rows, cols=cols)

        # Draw initial state
        self.grid_view.update(self.engine.grid.array)

    def toggle_play(self) -> bool:
        self.is_playing = not self.is_playing
        return self.is_playing

    def step_once(self) -> None:
        self.is_playing = False
        self.controls.force_pause()
        self._do_step()

    def reset_sim(self) -> None:
        self.engine.reset(self.initial_state)
        self.stats_view.reset()
        self.controls.clear_patterns()
        self.grid_view.update(self.engine.grid.array)

    def set_speed(self, speed: float) -> None:
        self.target_fps = speed

    def set_boundary(self, mode: BoundaryMode) -> None:
        self.config.boundary_mode = mode
        self.engine.config.boundary_mode = mode
        self.reset_sim()

    def _do_step(self) -> None:
        result = self.engine.step()
        self.grid_view.update(self.engine.grid.array)
        self.stats_view.update(
            result.iteration, result.live_cells, result.dead_cells, 
            result.execution_time_ms, result.is_stable
        )
        self.controls.add_patterns(result.iteration, result.detected_patterns)
        
        if result.is_stable and self.is_playing:
            self.is_playing = False
            self.controls.force_pause()

    def run(self) -> None:
        dpg.show_viewport()
        dpg.set_primary_window("Primary Window", True)
        
        while dpg.is_dearpygui_running():
            current_time = time.time()
            if self.is_playing and (current_time - self.last_update_time) >= (1.0 / self.target_fps):
                self._do_step()
                self.last_update_time = current_time
                
            dpg.render_dearpygui_frame()
            
        dpg.destroy_context()
