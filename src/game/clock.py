"""
Chess clock implementation.

Supports Fischer increment and multiple time control presets.
"""

from __future__ import annotations

import time
from src.utils.constants import TIME_CONTROLS, DEFAULT_TIME_CONTROL
from src.utils.helpers import format_time


class ChessClock:
    """Dual chess clock with optional Fischer increment."""

    def __init__(self, time_control: str = DEFAULT_TIME_CONTROL):
        base, increment = TIME_CONTROLS.get(time_control, TIME_CONTROLS[DEFAULT_TIME_CONTROL])
        self.base_time = base
        self.increment = increment
        self.white_time: float = float(base)
        self.black_time: float = float(base)
        self.unlimited = base == 0
        self._running = False
        self._white_turn = True
        self._last_tick: float = 0.0
        self._start_real_time: float = 0.0  # wall-clock start

    def start(self) -> None:
        """Start the clock (call after the first move)."""
        if not self.unlimited:
            self._running = True
            self._last_tick = time.time()
        self._start_real_time = time.time()

    def stop(self) -> None:
        """Pause the clock entirely."""
        self._update()
        self._running = False

    def switch(self) -> None:
        """Switch the active clock (call after each move)."""
        self._update()
        # Add increment to the player who just moved
        if self.increment and not self.unlimited:
            if self._white_turn:
                self.white_time += self.increment
            else:
                self.black_time += self.increment
        self._white_turn = not self._white_turn
        self._last_tick = time.time()

    def update(self) -> None:
        """Tick the clock — call each frame."""
        if self._running and not self.unlimited:
            self._update()

    def _update(self) -> None:
        now = time.time()
        elapsed = now - self._last_tick
        self._last_tick = now
        if self._white_turn:
            self.white_time = max(0.0, self.white_time - elapsed)
        else:
            self.black_time = max(0.0, self.black_time - elapsed)

    @property
    def white_display(self) -> str:
        if self.unlimited:
            return "∞"
        return format_time(self.white_time)

    @property
    def black_display(self) -> str:
        if self.unlimited:
            return "∞"
        return format_time(self.black_time)

    @property
    def is_white_flagged(self) -> bool:
        return not self.unlimited and self.white_time <= 0

    @property
    def is_black_flagged(self) -> bool:
        return not self.unlimited and self.black_time <= 0

    @property
    def is_flagged(self) -> bool:
        return self.is_white_flagged or self.is_black_flagged

    @property
    def active_color_name(self) -> str:
        return "White" if self._white_turn else "Black"

    @property
    def elapsed_seconds(self) -> float:
        """Total wall-clock time since the clock started."""
        if self._start_real_time == 0:
            return 0.0
        return time.time() - self._start_real_time

    def reset(self, time_control: str = DEFAULT_TIME_CONTROL) -> None:
        base, increment = TIME_CONTROLS.get(time_control, TIME_CONTROLS[DEFAULT_TIME_CONTROL])
        self.base_time = base
        self.increment = increment
        self.white_time = float(base)
        self.black_time = float(base)
        self.unlimited = base == 0
        self._running = False
        self._white_turn = True
        self._start_real_time = 0.0
