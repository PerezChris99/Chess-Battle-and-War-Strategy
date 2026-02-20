"""
Chess board renderer — draws the board, highlights, coordinates, and pieces.

War-themed aesthetic with parchment light squares and dark wood dark squares.
"""

from __future__ import annotations

import chess
import pygame

from src.utils.constants import (
    BOARD_SIZE, SQUARE_SIZE, BOARD_OFFSET_X, BOARD_OFFSET_Y,
    LIGHT_SQUARE, DARK_SQUARE, HIGHLIGHT_SQUARE, VALID_MOVE_DOT,
    LAST_MOVE_COLOR, CHECK_COLOR, TEXT_DIM, TEXT_GOLD,
)
from src.utils.helpers import algebraic_to_coords, board_to_pixel
from src.ui.piece_renderer import PieceRenderer


class BoardRenderer:
    """Renders the chess board, pieces, and all visual overlays."""

    def __init__(self):
        self.piece_renderer = PieceRenderer()
        self._coord_font: pygame.font.Font | None = None
        self._init_fonts()

    def _init_fonts(self) -> None:
        pygame.font.init()
        self._coord_font = pygame.font.SysFont("Consolas", 14, bold=True)

    def draw(
        self,
        screen: pygame.Surface,
        board: chess.Board,
        selected_square: int | None = None,
        valid_moves: list[chess.Move] | None = None,
        last_move: chess.Move | None = None,
        flipped: bool = False,
        drag_from: int | None = None,
        drag_piece: chess.Piece | None = None,
        drag_pos: tuple[int, int] | None = None,
        promoting: bool = False,
        promotion_square: int | None = None,
        player_color: chess.Color = chess.WHITE,
    ) -> None:
        """Draw the complete board with all overlays."""
        self._draw_squares(screen, flipped)
        self._draw_last_move(screen, last_move, flipped)
        self._draw_check(screen, board, flipped)
        self._draw_selected(screen, selected_square, flipped)
        self._draw_valid_moves(screen, valid_moves, flipped)
        self._draw_pieces(screen, board, flipped, drag_from)
        self._draw_coordinates(screen, flipped)

        # Draw drag piece on top
        if drag_piece and drag_pos:
            self.piece_renderer.draw_piece(
                screen, drag_piece.symbol(),
                drag_pos[0] - SQUARE_SIZE // 2,
                drag_pos[1] - SQUARE_SIZE // 2,
            )

        # Draw promotion chooser
        if promoting and promotion_square is not None:
            self._draw_promotion_ui(screen, promotion_square, player_color, flipped)

        # Border
        pygame.draw.rect(
            screen, (80, 70, 60),
            (BOARD_OFFSET_X - 2, BOARD_OFFSET_Y - 2,
             BOARD_SIZE + 4, BOARD_SIZE + 4),
            2,
        )

    # ── Board Drawing ───────────────────────────────────────────

    def _draw_squares(self, screen: pygame.Surface, flipped: bool) -> None:
        for row in range(8):
            for col in range(8):
                is_light = (col + row) % 2 == 0
                color = LIGHT_SQUARE if is_light else DARK_SQUARE
                x, y = board_to_pixel(col, row, BOARD_OFFSET_X, BOARD_OFFSET_Y, SQUARE_SIZE, flipped)
                pygame.draw.rect(screen, color, (x, y, SQUARE_SIZE, SQUARE_SIZE))

    def _draw_last_move(self, screen: pygame.Surface, last_move: chess.Move | None, flipped: bool) -> None:
        if not last_move:
            return
        overlay = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
        overlay.fill(LAST_MOVE_COLOR)
        for sq in [last_move.from_square, last_move.to_square]:
            col, row = algebraic_to_coords(sq)
            x, y = board_to_pixel(col, row, BOARD_OFFSET_X, BOARD_OFFSET_Y, SQUARE_SIZE, flipped)
            screen.blit(overlay, (x, y))

    def _draw_check(self, screen: pygame.Surface, board: chess.Board, flipped: bool) -> None:
        if not board.is_check():
            return
        king_sq = board.king(board.turn)
        if king_sq is not None:
            col, row = algebraic_to_coords(king_sq)
            x, y = board_to_pixel(col, row, BOARD_OFFSET_X, BOARD_OFFSET_Y, SQUARE_SIZE, flipped)
            overlay = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            overlay.fill(CHECK_COLOR)
            screen.blit(overlay, (x, y))

    def _draw_selected(self, screen: pygame.Surface, selected: int | None, flipped: bool) -> None:
        if selected is None:
            return
        col, row = algebraic_to_coords(selected)
        x, y = board_to_pixel(col, row, BOARD_OFFSET_X, BOARD_OFFSET_Y, SQUARE_SIZE, flipped)
        overlay = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
        overlay.fill(HIGHLIGHT_SQUARE)
        screen.blit(overlay, (x, y))

    def _draw_valid_moves(self, screen: pygame.Surface, moves: list[chess.Move] | None, flipped: bool) -> None:
        if not moves:
            return
        for move in moves:
            col, row = algebraic_to_coords(move.to_square)
            x, y = board_to_pixel(col, row, BOARD_OFFSET_X, BOARD_OFFSET_Y, SQUARE_SIZE, flipped)
            center = (x + SQUARE_SIZE // 2, y + SQUARE_SIZE // 2)
            # Draw dot for empty squares, ring for captures
            pygame.draw.circle(
                screen, VALID_MOVE_DOT[:3],
                center, SQUARE_SIZE // 6,
            )

    def _draw_pieces(
        self, screen: pygame.Surface,
        board: chess.Board,
        flipped: bool,
        skip_square: int | None = None,
    ) -> None:
        for sq in chess.SQUARES:
            if sq == skip_square:
                continue
            piece = board.piece_at(sq)
            if piece:
                col, row = algebraic_to_coords(sq)
                x, y = board_to_pixel(col, row, BOARD_OFFSET_X, BOARD_OFFSET_Y, SQUARE_SIZE, flipped)
                self.piece_renderer.draw_piece(screen, piece.symbol(), x, y)

    def _draw_coordinates(self, screen: pygame.Surface, flipped: bool) -> None:
        files = "abcdefgh"
        ranks = "12345678"
        if flipped:
            files = files[::-1]
            ranks = ranks[::-1]

        for i in range(8):
            # File labels (bottom)
            label = self._coord_font.render(files[i], True, TEXT_DIM)
            x = BOARD_OFFSET_X + i * SQUARE_SIZE + SQUARE_SIZE // 2 - label.get_width() // 2
            y = BOARD_OFFSET_Y + BOARD_SIZE + 4
            screen.blit(label, (x, y))

            # Rank labels (left)
            label = self._coord_font.render(ranks[7 - i], True, TEXT_DIM)
            x = BOARD_OFFSET_X - 18
            y = BOARD_OFFSET_Y + i * SQUARE_SIZE + SQUARE_SIZE // 2 - label.get_height() // 2
            screen.blit(label, (x, y))

    def _draw_promotion_ui(
        self, screen: pygame.Surface,
        square: int, color: chess.Color, flipped: bool,
    ) -> None:
        """Draw promotion piece selection overlay."""
        col, row = algebraic_to_coords(square)
        if flipped:
            col, row = 7 - col, 7 - row

        pieces = [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT]
        symbols = ["Q", "R", "B", "N"] if color == chess.WHITE else ["q", "r", "b", "n"]

        # Dim the board
        dim = pygame.Surface((BOARD_SIZE, BOARD_SIZE), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 120))
        screen.blit(dim, (BOARD_OFFSET_X, BOARD_OFFSET_Y))

        for i, sym in enumerate(symbols):
            y_offset = i if color == chess.WHITE else -i
            px = BOARD_OFFSET_X + col * SQUARE_SIZE
            py = BOARD_OFFSET_Y + (row + y_offset) * SQUARE_SIZE

            # Background
            bg_color = (60, 58, 50) if i % 2 == 0 else (80, 75, 65)
            pygame.draw.rect(screen, bg_color, (px, py, SQUARE_SIZE, SQUARE_SIZE))
            pygame.draw.rect(screen, TEXT_GOLD, (px, py, SQUARE_SIZE, SQUARE_SIZE), 2)

            # Piece
            self.piece_renderer.draw_piece(screen, sym, px, py)
