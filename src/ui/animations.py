"""
Move animation system.

Handles smooth piece movement animations between squares.
"""

from __future__ import annotations

import pygame
import chess
import time

from src.utils.constants import SQUARE_SIZE, BOARD_OFFSET_X, BOARD_OFFSET_Y, ANIMATION_DURATION
from src.utils.helpers import algebraic_to_coords, board_to_pixel


class Animation:
    """Single piece movement animation."""

    def __init__(
        self,
        piece_symbol: str,
        from_square: int,
        to_square: int,
        flipped: bool = False,
        duration: float = ANIMATION_DURATION,
    ):
        self.piece_symbol = piece_symbol
        self.from_square = from_square
        self.to_square = to_square
        self.flipped = flipped
        self.duration = duration
        self.start_time = time.time()
        self.done = False

        # Calculate pixel positions
        from_col, from_row = algebraic_to_coords(from_square)
        to_col, to_row = algebraic_to_coords(to_square)

        self.start_x, self.start_y = board_to_pixel(
            from_col, from_row, BOARD_OFFSET_X, BOARD_OFFSET_Y, SQUARE_SIZE, flipped,
        )
        self.end_x, self.end_y = board_to_pixel(
            to_col, to_row, BOARD_OFFSET_X, BOARD_OFFSET_Y, SQUARE_SIZE, flipped,
        )

    @property
    def progress(self) -> float:
        """0.0 → 1.0 progress of the animation."""
        elapsed = time.time() - self.start_time
        p = min(1.0, elapsed / self.duration)
        if p >= 1.0:
            self.done = True
        return p

    @property
    def current_pos(self) -> tuple[int, int]:
        """Current interpolated pixel position."""
        t = self._ease_out(self.progress)
        x = self.start_x + (self.end_x - self.start_x) * t
        y = self.start_y + (self.end_y - self.start_y) * t
        return int(x), int(y)

    @staticmethod
    def _ease_out(t: float) -> float:
        """Ease-out cubic for smooth deceleration."""
        return 1 - (1 - t) ** 3


class AnimationManager:
    """Manages active animations."""

    def __init__(self):
        self._animations: list[Animation] = []

    @property
    def is_animating(self) -> bool:
        return len(self._animations) > 0

    def add(self, animation: Animation) -> None:
        self._animations.append(animation)

    def update(self) -> list[Animation]:
        """Update animations and return completed ones."""
        completed = [a for a in self._animations if a.done]
        self._animations = [a for a in self._animations if not a.done]
        return completed

    def get_active(self) -> list[Animation]:
        """Get currently active animations (triggers progress calc)."""
        active = []
        for a in self._animations:
            _ = a.progress  # trigger update
            if not a.done:
                active.append(a)
        return active

    def clear(self) -> None:
        self._animations.clear()
