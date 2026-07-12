"""GUI Controls for the Game of Life."""

from typing import Any

import dearpygui.dearpygui as dpg  # type: ignore[import-untyped]

from libs.config import BoundaryMode, ComputeBackend


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
        on_backend_change: Any,
        on_all_cores_change: Any,
        max_fps: float,
        max_pattern_log_items: int = 50,
        visible_pattern_log_items: int = 6,
    ) -> None:
        self.max_fps = max_fps
        self.max_pattern_log_items = max_pattern_log_items
        self.on_play_pause = on_play_pause
        self.on_step = on_step
        self.on_reset = on_reset
        self.on_speed_change = on_speed_change
        self.on_boundary_change = on_boundary_change
        self.on_backend_change = on_backend_change
        self.on_all_cores_change = on_all_cores_change

        with dpg.group(parent=parent, horizontal=False):
            with dpg.group(horizontal=True):
                self.btn_play = dpg.add_button(label="Pause", callback=self._handle_play_pause)
                dpg.add_button(label="Step", callback=self.on_step)
                dpg.add_button(label="Reset", callback=self.on_reset)

            self.speed_slider = dpg.add_slider_int(
                label="Speed",
                default_value=10,
                min_value=1,
                max_value=int(self.max_fps),
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

            backend_items = [b.name for b in ComputeBackend]
            self.backend_combo = dpg.add_combo(
                label="Backend",
                items=backend_items,
                default_value=ComputeBackend.AUTO.name,
                callback=self._handle_backend_change,
            )
            self.backend_status = dpg.add_text("Backend: initializing...", color=[200, 200, 200])

            self.all_cores_checkbox = dpg.add_checkbox(
                label="Use All Cores (Disable P-Core affinity)",
                default_value=False,
                callback=self._handle_all_cores_change,
            )

            # Themes for explicitly coloring the checkbox text
            with dpg.theme() as self.disabled_theme:
                with dpg.theme_component(dpg.mvCheckbox):
                    dpg.add_theme_color(dpg.mvThemeCol_Text, [100, 100, 100, 255])

            with dpg.theme() as self.enabled_theme:
                with dpg.theme_component(dpg.mvCheckbox):
                    dpg.add_theme_color(dpg.mvThemeCol_Text, [200, 200, 200, 255])

            # Pattern log area
            dpg.add_separator()
            dpg.add_text("Detected Patterns:")
            self.pattern_log_container = dpg.add_child_window(
                width=-1, height=visible_pattern_log_items * 28
            )
            self._pattern_items: list[tuple[str, bool]] = []

    def _handle_speed_change(self, sender: Any, app_data: Any, user_data: Any) -> None:
        """Handle speed slider changes."""
        if app_data >= self.max_fps:
            dpg.configure_item(self.speed_slider, format="MAX (Uncapped)")
            dpg.set_value(self.text_speed_status, "Speed Limit: UNCAPPED (Max Performance)")
            dpg.configure_item(self.text_speed_status, color=[255, 100, 100])
        else:
            dpg.configure_item(self.speed_slider, format="%d Gen/s")
            dpg.set_value(self.text_speed_status, "Speed Limit: CAPPED")
            dpg.configure_item(self.text_speed_status, color=[200, 200, 200])
        self.on_speed_change(float(app_data))

    def _handle_play_pause(self, sender: Any, app_data: Any, user_data: Any) -> None:
        """Handle play/pause button click."""
        is_playing = self.on_play_pause()
        dpg.configure_item(self.btn_play, label="Pause" if is_playing else "Play")

    def _handle_backend_change(self, sender: Any, app_data: Any, user_data: Any) -> None:
        """Handle backend combo box selection."""
        selected = ComputeBackend[app_data]
        self.on_backend_change(selected)

    def _handle_all_cores_change(self, sender: Any, app_data: Any, user_data: Any) -> None:
        """Handle all cores checkbox toggle."""
        self.on_all_cores_change(bool(app_data))

    def set_all_cores_enabled(self, enabled: bool) -> None:
        """Enable or disable the all cores checkbox."""
        dpg.configure_item(self.all_cores_checkbox, enabled=enabled)
        if not enabled:
            dpg.set_value(self.all_cores_checkbox, False)
            dpg.bind_item_theme(self.all_cores_checkbox, self.disabled_theme)
        else:
            dpg.bind_item_theme(self.all_cores_checkbox, self.enabled_theme)

    def set_backend_status(self, text: str) -> None:
        """Update the backend status label below the combo box."""
        dpg.set_value(self.backend_status, text)

    def set_backend_combo(self, backend: ComputeBackend) -> None:
        """Set the backend combo box value without triggering the callback."""
        dpg.set_value(self.backend_combo, backend.name)

    def force_pause(self) -> None:
        """Force UI to display 'Play' because simulation was paused externally."""
        dpg.configure_item(self.btn_play, label="Play")

    def force_play(self) -> None:
        """Force UI to display 'Pause' because simulation was resumed externally."""
        dpg.configure_item(self.btn_play, label="Pause")

    def add_patterns(self, iteration: int, patterns: list[Any]) -> None:
        """Add newly detected patterns to the scrolling log."""
        if not patterns:
            return

        for p in patterns:
            msg = f"Gen {iteration}: {p.name} @ ({p.top_left_r}, {p.top_left_c})"
            self._pattern_items.insert(0, (msg, p.name == "Glider"))

        # Sort so that Gliders always stay at the top (True sorts before False)
        self._pattern_items.sort(key=lambda item: not item[1])

        # Keep only the max allowed patterns
        if len(self._pattern_items) > self.max_pattern_log_items:
            self._pattern_items = self._pattern_items[: self.max_pattern_log_items]

        self._render_pattern_log()

    def _render_pattern_log(self) -> None:
        dpg.delete_item(self.pattern_log_container, children_only=True)
        for msg, is_glider in self._pattern_items:
            color = [255, 50, 50, 255] if is_glider else [200, 200, 200, 255]
            dpg.add_text(msg, color=color, parent=self.pattern_log_container)

    def clear_patterns(self) -> None:
        """Clear the pattern log."""
        self._pattern_items.clear()
        self._render_pattern_log()
