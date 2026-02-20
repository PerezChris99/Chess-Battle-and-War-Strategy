"""
Utility helper functions used across the project.

Coordinate conversions, formatting, material counting, etc.
"""

from __future__ import annotations

import chess
from .constants import PIECE_VALUES


# ─────────────────────────────────────────────────────────────────────────────
# Coordinate Helpers
# ─────────────────────────────────────────────────────────────────────────────

def algebraic_to_coords(square: int) -> tuple[int, int]:
    """Convert python-chess square index (0-63) → (col, row) for rendering."""
    return chess.square_file(square), 7 - chess.square_rank(square)


def coords_to_square(col: int, row: int) -> int:
    """Convert board grid (col, row) → python-chess square index."""
    return chess.square(col, 7 - row)


def pixel_to_board(
    x: int, y: int,
    offset_x: int, offset_y: int,
    square_size: int,
    flipped: bool = False,
) -> tuple[int, int] | None:
    """Convert screen pixel → board (col, row).  Returns None if off-board."""
    col = (x - offset_x) // square_size
    row = (y - offset_y) // square_size
    if not (0 <= col < 8 and 0 <= row < 8):
        return None
    if flipped:
        col, row = 7 - col, 7 - row
    return col, row


def board_to_pixel(
    col: int, row: int,
    offset_x: int, offset_y: int,
    square_size: int,
    flipped: bool = False,
) -> tuple[int, int]:
    """Convert board (col, row) → top-left pixel of that square."""
    if flipped:
        col, row = 7 - col, 7 - row
    return offset_x + col * square_size, offset_y + row * square_size


# ─────────────────────────────────────────────────────────────────────────────
# Formatting
# ─────────────────────────────────────────────────────────────────────────────

def format_time(seconds: float) -> str:
    """Format seconds → 'MM:SS'."""
    s = max(0, int(seconds))
    return f"{s // 60:02d}:{s % 60:02d}"


def piece_full_name(symbol: str) -> str:
    """'N' → 'Knight', 'q' → 'Queen', etc."""
    _map = {
        "K": "King",   "Q": "Queen",  "R": "Rook",
        "B": "Bishop", "N": "Knight", "P": "Pawn",
    }
    return _map.get(symbol.upper(), "Unknown")


def square_name(sq: int) -> str:
    """python-chess square → 'e4', 'a1', etc."""
    return chess.square_name(sq)


def is_light_square(col: int, row: int) -> bool:
    return (col + row) % 2 == 0


# ─────────────────────────────────────────────────────────────────────────────
# Material Helpers
# ─────────────────────────────────────────────────────────────────────────────

def get_material_balance(board: chess.Board) -> int:
    """Return material balance in centipawns (positive = White ahead)."""
    balance = 0
    for sq in chess.SQUARES:
        piece = board.piece_at(sq)
        if piece:
            val = PIECE_VALUES.get(piece.symbol(), 0)
            balance += val if piece.color == chess.WHITE else -val
    return balance


def get_captured_pieces(board: chess.Board) -> tuple[list[str], list[str]]:
    """Return (white_captured, black_captured) — pieces removed from the board.

    white_captured  = white pieces taken by black  (lowercase symbols)
    black_captured  = black pieces taken by white   (uppercase symbols)
    """
    initial = {"P": 8, "N": 2, "B": 2, "R": 2, "Q": 1}
    w_rem = {p: 0 for p in initial}
    b_rem = {p: 0 for p in initial}

    for sq in chess.SQUARES:
        piece = board.piece_at(sq)
        if piece:
            sym = piece.symbol().upper()
            if sym in initial:
                if piece.color == chess.WHITE:
                    w_rem[sym] += 1
                else:
                    b_rem[sym] += 1

    white_captured: list[str] = []
    black_captured: list[str] = []
    for p, cnt in initial.items():
        white_captured.extend([p.lower()] * (cnt - w_rem[p]))
        black_captured.extend([p]         * (cnt - b_rem[p]))

    return white_captured, black_captured


def get_game_phase(board: chess.Board) -> str:
    """Rough game phase: 'opening', 'middlegame', or 'endgame'."""
    total_material = 0
    for sq in chess.SQUARES:
        p = board.piece_at(sq)
        if p and p.symbol().upper() != "K":
            total_material += PIECE_VALUES.get(p.symbol(), 0)
    if total_material > 6200:
        return "opening"
    elif total_material > 3000:
        return "middlegame"
    return "endgame"


def is_endgame(board: chess.Board) -> bool:
    return get_game_phase(board) == "endgame"


def count_pieces(board: chess.Board) -> int:
    """Total non-king pieces on the board."""
    return sum(
        1 for sq in chess.SQUARES
        if board.piece_at(sq) and board.piece_at(sq).symbol().upper() != "K"
    )
