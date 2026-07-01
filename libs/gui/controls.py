"""GUI Controls for the Game of Life."""

import dearpygui.dearpygui as dpg

from game_of_life.config import BoundaryMode


class Controls:
    """Manages the interactive controls of the GUI."""

    def __init__(
        self,
        parent: int | str,
        on_play_pause,
        on_step,
        on_reset,
        on_speed_change,
        on_boundary_change,
    ):
        self.on_play_pause = on_play_pause
        self.on_step = on_step
        self.on_reset = on_reset
        self.on_speed_change = on_speed_change
        self.on_boundary_change = on_boundary_change

        with dpg.group(parent=parent, horizontal=False):
            with dpg.group(horizontal=True):
                self.btn_play = dpg.add_button(label="Pause", callback=self._handle_play_pause)
                dpg.add_button(label="Step", callback=self.on_step)
                dpg.add_button(label="Reset", callback=self.on_reset)

            dpg.add_slider_float(
                label="Speed (Gen/s)",
                default_value=10.0,
                min_value=1.0,
                max_value=60.0,
                callback=lambda s, a, u: self.on_speed_change(a),
            )

            dpg.add_combo(
                label="Boundary Mode",
                items=[BoundaryMode.TOROIDAL.name, BoundaryMode.BOUNDED.name],
                default_value=BoundaryMode.TOROIDAL.name,
                callback=lambda s, a, u: self.on_boundary_change(BoundaryMode[a]),
            )

            # Pattern log area
            dpg.add_separator()
            dpg.add_text("Detected Patterns:")
            self.pattern_listbox = dpg.add_listbox(items=[], width=-1, num_items=6)
            self._pattern_items = []

    def _handle_play_pause(self, sender, app_data, user_data) -> None:
        is_playing = self.on_play_pause()
        dpg.configure_item(self.btn_play, label="Pause" if is_playing else "Play")

    def force_pause(self) -> None:
        """Force UI to display 'Play' because simulation was paused externally."""
        dpg.configure_item(self.btn_play, label="Play")

    def add_patterns(self, iteration: int, patterns: list) -> None:
        """Add newly detected patterns to the scrolling log."""
        if not patterns:
            return

        for p in patterns:
            msg = f"Gen {iteration}: {p.name} @ ({p.top_left_r}, {p.top_left_c})"
            self._pattern_items.insert(0, msg)

        # Keep only the last 50
        if len(self._pattern_items) > 50:
            self._pattern_items = self._pattern_items[:50]

        dpg.configure_item(self.pattern_listbox, items=self._pattern_items)

    def clear_patterns(self) -> None:
        """Clear the pattern log."""
        self._pattern_items.clear()
        dpg.configure_item(self.pattern_listbox, items=self._pattern_items)
