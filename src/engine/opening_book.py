"""
Magnus Carlsen's Opening Book.

Contains key opening lines from Magnus's repertoire, stored as move sequences.
The AI will follow book moves in the opening phase for authentic play.

As White — Magnus commonly plays:
  • 1.e4 → Ruy Lopez, Italian Game, Scotch
  • 1.d4 → Catalan, Queen's Gambit
  • 1.c4 → English Opening
  • 1.Nf3 → Reti Opening

As Black — Magnus commonly responds:
  • vs 1.e4 → Sicilian (Sveshnikov, Najdorf), Berlin Defense
  • vs 1.d4 → Nimzo-Indian, QGD, Grünfeld
"""

from __future__ import annotations

import chess
import random
from typing import Optional


class OpeningBook:
    """Opening book based on Magnus Carlsen's tournament repertoire."""

    def __init__(self):
        self._book = self._build_book()

    def get_move(self, board: chess.Board) -> Optional[chess.Move]:
        """Return a book move for the current position, or None."""
        key = self._position_key(board)
        if key in self._book:
            candidates = self._book[key]
            # Weighted random selection (first moves have higher weight)
            weights = [entry["weight"] for entry in candidates]
            total = sum(weights)
            r = random.random() * total
            cumulative = 0
            for entry in candidates:
                cumulative += entry["weight"]
                if r <= cumulative:
                    move = chess.Move.from_uci(entry["uci"])
                    if move in board.legal_moves:
                        return move
                    break
        return None

    @staticmethod
    def _position_key(board: chess.Board) -> str:
        """Create a hashable key from the move sequence (for simple book lookup)."""
        return " ".join(m.uci() for m in board.move_stack)

    def _build_book(self) -> dict:
        """Build the opening book dictionary.

        Keys are space-separated UCI move sequences.
        Values are lists of {uci, weight, name} dictionaries.
        """
        book = {}

        def add_line(moves_uci: list[str], name: str, base_weight: int = 10) -> None:
            """Register an opening line in the book."""
            for i in range(len(moves_uci)):
                key = " ".join(moves_uci[:i])
                uci = moves_uci[i]
                if key not in book:
                    book[key] = []
                # Avoid duplicates
                if not any(e["uci"] == uci for e in book[key]):
                    book[key].append({
                        "uci": uci,
                        "weight": base_weight,
                        "name": name,
                    })

        # ═══════════════════════════════════════════════════════
        #  WHITE REPERTOIRE (Magnus as White)
        # ═══════════════════════════════════════════════════════

        # ── Ruy Lopez (Magnus's most played opening) ──────────
        add_line(
            ["e2e4", "e7e5", "g1f3", "b8c6", "f1b5"],
            "Ruy Lopez", 15
        )
        # Ruy Lopez — Berlin Defense (Magnus's specialty)
        add_line(
            ["e2e4", "e7e5", "g1f3", "b8c6", "f1b5", "g8f6", "e1g1"],
            "Ruy Lopez — Berlin", 14
        )
        # Ruy Lopez — Closed (classical approach)
        add_line(
            ["e2e4", "e7e5", "g1f3", "b8c6", "f1b5", "a7a6", "b5a4", "g8f6", "e1g1"],
            "Ruy Lopez — Closed", 13
        )
        # Ruy Lopez — Marshall Attack refusal
        add_line(
            ["e2e4", "e7e5", "g1f3", "b8c6", "f1b5", "a7a6", "b5a4", "g8f6",
             "e1g1", "f8e7", "f1e1", "b7b5", "a4b3", "e8g8", "c2c3"],
            "Ruy Lopez — Anti-Marshall", 12
        )

        # ── Italian Game ──────────────────────────────────────
        add_line(
            ["e2e4", "e7e5", "g1f3", "b8c6", "f1c4"],
            "Italian Game", 12
        )
        add_line(
            ["e2e4", "e7e5", "g1f3", "b8c6", "f1c4", "f8c5", "c2c3"],
            "Italian — Giuoco Piano", 11
        )

        # ── Scotch Game ───────────────────────────────────────
        add_line(
            ["e2e4", "e7e5", "g1f3", "b8c6", "d2d4"],
            "Scotch Game", 8
        )

        # ── Queen's Gambit ────────────────────────────────────
        add_line(
            ["d2d4", "d7d5", "c2c4"],
            "Queen's Gambit", 14
        )
        add_line(
            ["d2d4", "d7d5", "c2c4", "e7e6", "b1c3", "g8f6", "c1g5"],
            "QGD — Classical", 12
        )
        add_line(
            ["d2d4", "d7d5", "c2c4", "e7e6", "g1f3", "g8f6", "g2g3"],
            "QGD — Catalan Setup", 13
        )

        # ── Catalan Opening (Magnus's favorite with d4) ───────
        add_line(
            ["d2d4", "g8f6", "c2c4", "e7e6", "g2g3"],
            "Catalan Opening", 14
        )
        add_line(
            ["d2d4", "g8f6", "c2c4", "e7e6", "g2g3", "d7d5", "f1g2", "f8e7", "g1f3"],
            "Catalan — Closed", 13
        )
        add_line(
            ["d2d4", "g8f6", "c2c4", "e7e6", "g2g3", "d7d5", "f1g2", "d5c4", "d1a4"],
            "Catalan — Open", 12
        )

        # ── English Opening ───────────────────────────────────
        add_line(
            ["c2c4", "e7e5", "b1c3"],
            "English Opening", 8
        )
        add_line(
            ["c2c4", "g8f6", "b1c3", "e7e5"],
            "English — Reversed Sicilian", 7
        )

        # ── Reti Opening ──────────────────────────────────────
        add_line(
            ["g1f3", "d7d5", "g2g3"],
            "Reti Opening", 6
        )

        # ── London System (Magnus occasionally) ───────────────
        add_line(
            ["d2d4", "d7d5", "c1f4"],
            "London System", 5
        )

        # ═══════════════════════════════════════════════════════
        #  BLACK REPERTOIRE (Magnus as Black)
        # ═══════════════════════════════════════════════════════

        # ── vs 1.e4 — Sicilian Defense (Sveshnikov) ──────────
        add_line(
            ["e2e4", "c7c5"],
            "Sicilian Defense", 13
        )
        add_line(
            ["e2e4", "c7c5", "g1f3", "b8c6", "d2d4", "c5d4", "f3d4", "g8f6", "b1c3", "e7e5"],
            "Sicilian — Sveshnikov", 12
        )

        # ── vs 1.e4 — Sicilian Najdorf ───────────────────────
        add_line(
            ["e2e4", "c7c5", "g1f3", "d7d6", "d2d4", "c5d4", "f3d4", "g8f6", "b1c3", "a7a6"],
            "Sicilian — Najdorf", 11
        )

        # ── vs 1.e4 — Berlin Defense ─────────────────────────
        add_line(
            ["e2e4", "e7e5", "g1f3", "b8c6", "f1b5", "g8f6"],
            "Berlin Defense", 14
        )

        # ── vs 1.d4 — Nimzo-Indian ───────────────────────────
        add_line(
            ["d2d4", "g8f6", "c2c4", "e7e6", "b1c3", "f8b4"],
            "Nimzo-Indian", 13
        )

        # ── vs 1.d4 — Queen's Gambit Declined ────────────────
        add_line(
            ["d2d4", "d7d5", "c2c4", "e7e6", "b1c3", "g8f6"],
            "QGD", 12
        )
        add_line(
            ["d2d4", "d7d5", "c2c4", "e7e6", "b1c3", "g8f6", "c4d5", "e6d5"],
            "QGD — Exchange", 10
        )

        # ── vs 1.d4 — Grünfeld Defense ───────────────────────
        add_line(
            ["d2d4", "g8f6", "c2c4", "g7g6", "b1c3", "d7d5"],
            "Grünfeld Defense", 10
        )

        # ── vs 1.c4 — Symmetrical English ────────────────────
        add_line(
            ["c2c4", "c7c5"],
            "Symmetrical English", 9
        )

        # ── vs 1.Nf3 ─────────────────────────────────────────
        add_line(
            ["g1f3", "d7d5", "g2g3", "g8f6"],
            "vs Reti — Classical", 8
        )

        # ── Opening first moves (root position) ──────────────
        # Magnus's first move preferences as White
        if "" not in book:
            book[""] = []
        book[""] = [
            {"uci": "e2e4", "weight": 15, "name": "King's Pawn"},
            {"uci": "d2d4", "weight": 14, "name": "Queen's Pawn"},
            {"uci": "c2c4", "weight": 6,  "name": "English"},
            {"uci": "g1f3", "weight": 5,  "name": "Reti"},
        ]

        return book

    def get_opening_name(self, board: chess.Board) -> Optional[str]:
        """Return the name of the current opening line, if in book."""
        key = self._position_key(board)
        # Walk backwards to find the deepest named position
        moves = list(board.move_stack)
        for i in range(len(moves), 0, -1):
            partial_key = " ".join(m.uci() for m in moves[:i])
            if partial_key in self._book:
                for entry in self._book[partial_key]:
                    return entry["name"]
        if "" in self._book and board.move_stack:
            first = board.move_stack[0].uci()
            for entry in self._book[""]:
                if entry["uci"] == first:
                    return entry["name"]
        return None
