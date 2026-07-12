"""Dear PyGui views for the Game of Life."""

import dearpygui.dearpygui as dpg  # type: ignore[import-untyped]
import numpy as np


class GridView:
    """Manages the heat series rendering of the cellular automaton grid."""

    def __init__(self, parent: int | str, rows: int, cols: int):
        self.rows = rows
        self.cols = cols

        with dpg.plot(
            label="Game of Life Grid",
            width=-1,
            height=-1,
            parent=parent,
            equal_aspects=True,
            no_menus=True,
            no_title=True,
        ) as self.plot_id:
            self.x_axis = dpg.add_plot_axis(
                dpg.mvXAxis, no_gridlines=True, no_tick_marks=True, no_tick_labels=True
            )
            self.y_axis = dpg.add_plot_axis(
                dpg.mvYAxis, no_gridlines=True, no_tick_marks=True, no_tick_labels=True
            )

            # The heat series expects a flat list of floats, normalized between scale limits
            # Note: Dear PyGui heat series takes data in row-major depending on version.
            # but usually it's just a flattened 1D list of the 2D array.
            dummy_data = [0.0] * (rows * cols)
            self.series_id = dpg.add_heat_series(
                dummy_data,
                rows=rows,
                cols=cols,
                scale_min=0,
                scale_max=1,
                parent=self.y_axis,
                format="",
            )

            # Use a custom colormap (Black for 0, Green for 1)
            with dpg.colormap_registry():
                self.colormap = dpg.add_colormap(
                    [
                        [20, 20, 20, 255],  # Dead: Dark gray/black
                        [0, 255, 100, 255],  # Alive: Bright green
                    ],
                    qualitative=True,
                )
                dpg.bind_colormap(self.plot_id, self.colormap)

    def update(self, grid_array: np.ndarray) -> None:
        """Update the heat series with the new grid data."""
        # Convert uint8 to float, flatten.
        # Dear PyGui's heat series expects a flat list of floats.
        # We might need to flip the array depending on coordinate systems.
        # Often, dpg expects data row by row from top to bottom or bottom to top.
        # Assuming standard top-left to bottom-right flattened:
        flat_data = grid_array.flatten().astype(float).tolist()
        dpg.set_value(self.series_id, [flat_data, [0.0, 1.0]])


class StatsView:
    """Manages the rolling line plot of live cells over time and text readouts."""

    def __init__(self, parent: int | str):
        self.max_history = 200
        self.iterations: list[float] = []
        self.live_cells: list[float] = []

        with dpg.group(parent=parent):
            self.text_backend = dpg.add_text("Backend: Unknown", color=[100, 200, 255])
            self.text_topology = dpg.add_text("Topology: Unknown", color=[200, 200, 100])
            self.text_iter = dpg.add_text("Iteration: 0")
            self.text_live = dpg.add_text("Live Cells: 0")
            self.text_dead = dpg.add_text("Dead Cells: 0")
            self.text_time = dpg.add_text("Step Time (ms): 0.00")
            self.text_status = dpg.add_text("Status: Running", color=[0, 255, 0])

            with dpg.plot(label="Population History", height=150, width=-1, no_menus=True):
                self.x_axis = dpg.add_plot_axis(dpg.mvXAxis, label="Iteration")
                self.y_axis = dpg.add_plot_axis(dpg.mvYAxis, label="Live Cells")
                self.line_series = dpg.add_line_series([], [], parent=self.y_axis)

    def update(self, iteration: int, live: int, dead: int, time_ms: float, is_stable: bool) -> None:
        """Update text readouts and the rolling plot."""
        dpg.set_value(self.text_iter, f"Iteration: {iteration}")
        dpg.set_value(self.text_live, f"Live Cells: {live}")
        dpg.set_value(self.text_dead, f"Dead Cells: {dead}")
        dpg.set_value(self.text_time, f"Step Time (ms): {time_ms:.2f}")

        if is_stable:
            dpg.set_value(self.text_status, "Status: STABLE (Auto-Paused)")
            dpg.configure_item(self.text_status, color=[255, 100, 100])
        else:
            dpg.set_value(self.text_status, "Status: Running")
            dpg.configure_item(self.text_status, color=[0, 255, 0])

        self.iterations.append(float(iteration))
        self.live_cells.append(float(live))

        if len(self.iterations) > self.max_history:
            self.iterations.pop(0)
            self.live_cells.pop(0)

        dpg.set_value(self.line_series, [self.iterations, self.live_cells])
        dpg.fit_axis_data(self.x_axis)
        dpg.fit_axis_data(self.y_axis)

    def reset(self) -> None:
        """Clear history on reset."""
        self.iterations.clear()
        self.live_cells.clear()
        dpg.set_value(self.line_series, [[], []])
        dpg.set_value(self.text_status, "Status: Running")
        dpg.configure_item(self.text_status, color=[0, 255, 0])

    def set_backend(self, text: str) -> None:
        """Update the backend text readout."""
        dpg.set_value(self.text_backend, f"Backend: {text}")

    def set_topology(self, text: str) -> None:
        """Update the topology text readout."""
        dpg.set_value(self.text_topology, f"Topology: {text}")
