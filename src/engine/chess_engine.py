"""
Chess engine wrapper around python-chess.

Provides a clean interface for game logic, move generation, validation,
and board state queries used by the rest of the application.
"""

from __future__ import annotations

import chess
import chess.pgn
import io
from typing import Optional


class ChessEngine:
    """High-level wrapper around a python-chess Board."""

    def __init__(self, fen: str | None = None):
        self.board = chess.Board(fen) if fen else chess.Board()
        self._move_stack_san: list[str] = []

    # ── State Queries ───────────────────────────────────────────

    @property
    def turn(self) -> chess.Color:
        return self.board.turn

    @property
    def turn_name(self) -> str:
        return "White" if self.board.turn == chess.WHITE else "Black"

    @property
    def fullmove_number(self) -> int:
        return self.board.fullmove_number

    @property
    def is_check(self) -> bool:
        return self.board.is_check()

    @property
    def is_checkmate(self) -> bool:
        return self.board.is_checkmate()

    @property
    def is_stalemate(self) -> bool:
        return self.board.is_stalemate()

    @property
    def is_game_over(self) -> bool:
        return self.board.is_game_over()

    @property
    def result(self) -> str:
        return self.board.result()

    @property
    def fen(self) -> str:
        return self.board.fen()

    @property
    def legal_moves(self) -> list[chess.Move]:
        return list(self.board.legal_moves)

    @property
    def move_count(self) -> int:
        return len(self.board.move_stack)

    # ── Move Operations ─────────────────────────────────────────

    def get_legal_moves_from(self, square: int) -> list[chess.Move]:
        """Get all legal moves originating from the given square."""
        return [m for m in self.board.legal_moves if m.from_square == square]

    def is_legal(self, move: chess.Move) -> bool:
        return move in self.board.legal_moves

    def make_move(self, move: chess.Move) -> str:
        """Execute a move. Returns the SAN notation string."""
        san = self.board.san(move)
        self.board.push(move)
        self._move_stack_san.append(san)
        return san

    def make_move_uci(self, uci: str) -> str:
        """Execute a move from UCI string (e.g., 'e2e4'). Returns SAN."""
        move = chess.Move.from_uci(uci)
        return self.make_move(move)

    def undo_move(self) -> Optional[chess.Move]:
        """Undo the last move. Returns the move that was undone."""
        if self.board.move_stack:
            self._move_stack_san.pop()
            return self.board.pop()
        return None

    def is_promotion_move(self, from_sq: int, to_sq: int) -> bool:
        """Check whether moving from → to would be a pawn promotion."""
        piece = self.board.piece_at(from_sq)
        if piece and piece.piece_type == chess.PAWN:
            rank = chess.square_rank(to_sq)
            if (piece.color == chess.WHITE and rank == 7) or \
               (piece.color == chess.BLACK and rank == 0):
                return True
        return False

    def create_promotion_move(
        self, from_sq: int, to_sq: int,
        promotion: int = chess.QUEEN,
    ) -> chess.Move:
        return chess.Move(from_sq, to_sq, promotion=promotion)

    # ── Board Queries ───────────────────────────────────────────

    def piece_at(self, square: int) -> Optional[chess.Piece]:
        return self.board.piece_at(square)

    def piece_symbol_at(self, square: int) -> Optional[str]:
        p = self.board.piece_at(square)
        return p.symbol() if p else None

    def king_square(self, color: chess.Color) -> int:
        return self.board.king(color)

    def is_capture(self, move: chess.Move) -> bool:
        return self.board.is_capture(move)

    def is_castling(self, move: chess.Move) -> bool:
        return self.board.is_castling(move)

    def is_en_passant(self, move: chess.Move) -> bool:
        return self.board.is_en_passant(move)

    def is_kingside_castling(self, move: chess.Move) -> bool:
        return self.board.is_kingside_castling(move)

    def is_queenside_castling(self, move: chess.Move) -> bool:
        return self.board.is_queenside_castling(move)

    def gives_check(self, move: chess.Move) -> bool:
        return self.board.gives_check(move)

    def last_move(self) -> Optional[chess.Move]:
        return self.board.peek() if self.board.move_stack else None

    # ── Notation ────────────────────────────────────────────────

    def san(self, move: chess.Move) -> str:
        return self.board.san(move)

    def san_history(self) -> list[str]:
        return list(self._move_stack_san)

    def to_pgn(self, white: str = "Player", black: str = "AI") -> str:
        """Export the current game as PGN text."""
        game = chess.pgn.Game()
        game.headers["White"] = white
        game.headers["Black"] = black
        game.headers["Result"] = self.board.result()
        node = game
        temp = chess.Board()
        for move in self.board.move_stack:
            node = node.add_variation(move)
            temp.push(move)
        sio = io.StringIO()
        exporter = chess.pgn.FileExporter(sio)
        game.accept(exporter)
        return sio.getvalue()

    # ── Reset ───────────────────────────────────────────────────

    def new_game(self, fen: str | None = None) -> None:
        self.board = chess.Board(fen) if fen else chess.Board()
        self._move_stack_san.clear()

    def copy(self) -> "ChessEngine":
        """Return a deep copy for analysis / search."""
        eng = ChessEngine.__new__(ChessEngine)
        eng.board = self.board.copy()
        eng._move_stack_san = list(self._move_stack_san)
        return eng
