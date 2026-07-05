"""GUI Controls for the Game of Life."""

from typing import Any

import dearpygui.dearpygui as dpg  # type: ignore[import-untyped]

from libs.config import BoundaryMode


class Controls:
    """Manages the interactive controls of the GUI."""

    def __init__(
        self,
        parent: int | str,
        on_play_pause: Any,
        on_step: Any,
        on_reset: Any,
        on_speed_change: Any,
        on_boundary_change: Any,
    ) -> None:
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

            self.speed_slider = dpg.add_slider_int(
                label="Speed",
                default_value=10,
                min_value=1,
                max_value=1000,
                format="%d Gen/s",
                callback=self._handle_speed_change,
            )
            self.text_speed_status = dpg.add_text("Speed Limit: CAPPED", color=[200, 200, 200])

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
            self._pattern_items: list[str] = []

    def _handle_speed_change(self, sender: Any, app_data: Any, user_data: Any) -> None:
        if app_data >= 1000:
            dpg.configure_item(self.speed_slider, format="MAX (Uncapped)")
            dpg.set_value(self.text_speed_status, "Speed Limit: UNCAPPED (Max Performance)")
            dpg.configure_item(self.text_speed_status, color=[255, 100, 100])
        else:
            dpg.configure_item(self.speed_slider, format="%d Gen/s")
            dpg.set_value(self.text_speed_status, "Speed Limit: CAPPED")
            dpg.configure_item(self.text_speed_status, color=[200, 200, 200])
        self.on_speed_change(float(app_data))

    def _handle_play_pause(self, sender: Any, app_data: Any, user_data: Any) -> None:
        is_playing = self.on_play_pause()
        dpg.configure_item(self.btn_play, label="Pause" if is_playing else "Play")

    def force_pause(self) -> None:
        """Force UI to display 'Play' because simulation was paused externally."""
        dpg.configure_item(self.btn_play, label="Play")

    def add_patterns(self, iteration: int, patterns: list[Any]) -> None:
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
