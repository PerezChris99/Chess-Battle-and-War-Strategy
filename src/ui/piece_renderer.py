"""
Chess piece renderer — draws pieces using Unicode symbols with Pygame fonts.

Supports both light and dark pieces with outlines for visibility.
Falls back to letter-based rendering if Unicode glyphs are unavailable.
"""

from __future__ import annotations

import pygame
import sys
from src.utils.constants import (
    SQUARE_SIZE, UNICODE_PIECES,
    WHITE_PIECE_COLOR, WHITE_PIECE_OUTLINE,
    BLACK_PIECE_COLOR, BLACK_PIECE_OUTLINE,
)


class PieceRenderer:
    """Renders chess pieces as styled Unicode glyphs."""

    def __init__(self):
        self._piece_cache: dict[str, pygame.Surface] = {}
        self._font: pygame.font.Font | None = None
        self._font_size = int(SQUARE_SIZE * 0.78)
        self._init_font()

    def _init_font(self) -> None:
        """Initialize the best available font for chess symbols."""
        pygame.font.init()
        # Try fonts known to have good chess Unicode support
        preferred = [
            "Segoe UI Symbol",    # Windows
            "Arial Unicode MS",   # Windows/Mac
            "DejaVu Sans",        # Linux
            "Noto Sans Symbols2", # Linux
            "Apple Symbols",      # Mac
        ]
        for name in preferred:
            try:
                self._font = pygame.font.SysFont(name, self._font_size)
                # Test if it can render a chess piece
                test = self._font.render("♔", True, (255, 255, 255))
                if test.get_width() > 5:
                    return
            except Exception:
                continue

        # Fallback to default font
        self._font = pygame.font.SysFont(None, self._font_size)

    def get_piece_surface(self, symbol: str) -> pygame.Surface:
        """Get a rendered piece surface (cached).

        Args:
            symbol: Piece symbol like 'K', 'q', 'N', 'p', etc.
        """
        if symbol in self._piece_cache:
            return self._piece_cache[symbol]

        surface = self._render_piece(symbol)
        self._piece_cache[symbol] = surface
        return surface

    def _render_piece(self, symbol: str) -> pygame.Surface:
        """Render a single piece to a surface with outline effect."""
        unicode_char = UNICODE_PIECES.get(symbol, symbol)
        is_white = symbol.isupper()

        if is_white:
            color = WHITE_PIECE_COLOR
            outline = WHITE_PIECE_OUTLINE
        else:
            color = BLACK_PIECE_COLOR
            outline = BLACK_PIECE_OUTLINE

        size = SQUARE_SIZE
        surface = pygame.Surface((size, size), pygame.SRCALPHA)

        # Render outline (draw text in 8 directions offset by 2px)
        outline_offsets = [(-2, -2), (-2, 0), (-2, 2), (0, -2),
                          (0, 2), (2, -2), (2, 0), (2, 2)]
        for dx, dy in outline_offsets:
            glyph = self._font.render(unicode_char, True, outline)
            rect = glyph.get_rect(center=(size // 2 + dx, size // 2 + dy))
            surface.blit(glyph, rect)

        # Render main glyph
        glyph = self._font.render(unicode_char, True, color)
        rect = glyph.get_rect(center=(size // 2, size // 2))
        surface.blit(glyph, rect)

        return surface

    def draw_piece(
        self, screen: pygame.Surface,
        symbol: str, x: int, y: int,
        alpha: int = 255,
    ) -> None:
        """Draw a piece at pixel position (x, y)."""
        surf = self.get_piece_surface(symbol)
        if alpha < 255:
            surf = surf.copy()
            surf.set_alpha(alpha)
        screen.blit(surf, (x, y))

    def clear_cache(self) -> None:
        """Clear the piece surface cache (e.g. on resize)."""
        self._piece_cache.clear()
