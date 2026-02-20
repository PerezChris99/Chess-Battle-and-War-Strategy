"""
Save/load manager — PGN export, import, and game state persistence.

Handles saving games as PGN files with battle narrative annotations,
loading PGN games for review, and auto-save functionality.
"""

from __future__ import annotations

import chess
import chess.pgn
import io
import os
import time
from datetime import datetime
from typing import Optional

from src.game.move_history import MoveHistory
from src.utils.constants import PROJECT_ROOT


# Default save directory
SAVES_DIR = os.path.join(PROJECT_ROOT, "saves")


class SaveLoadManager:
    """Manages game saves and loads in PGN format."""

    def __init__(self):
        os.makedirs(SAVES_DIR, exist_ok=True)

    # ── Save ────────────────────────────────────────────────────

    def save_game(
        self,
        board: chess.Board,
        history: MoveHistory,
        player_color: str = "white",
        difficulty: str = "SOLDIER",
        opening_name: str = "",
        result: str = "*",
        filename: str | None = None,
    ) -> str:
        """Save the current game as a PGN file. Returns the filepath."""
        game = chess.pgn.Game()

        # Headers
        game.headers["Event"] = "Chess Battle & War Strategy"
        game.headers["Site"] = "Local"
        game.headers["Date"] = datetime.now().strftime("%Y.%m.%d")
        game.headers["Round"] = "1"
        game.headers["White"] = "Player" if player_color == "white" else f"AI ({difficulty})"
        game.headers["Black"] = f"AI ({difficulty})" if player_color == "white" else "Player"
        game.headers["Result"] = result
        if opening_name:
            game.headers["Opening"] = opening_name

        # Replay moves onto the PGN game tree
        node = game
        replay = chess.Board()
        for record in history.moves:
            move = chess.Move.from_uci(record.uci)
            if move in replay.legal_moves:
                node = node.add_variation(move)
                # Add narrative as comment
                if record.narrative:
                    node.comment = record.narrative
                replay.push(move)

        # Determine filename
        if not filename:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            difficulty_tag = difficulty.lower()
            filename = f"battle_{ts}_{difficulty_tag}.pgn"

        filepath = os.path.join(SAVES_DIR, filename)

        # Write PGN
        with open(filepath, "w", encoding="utf-8") as f:
            exporter = chess.pgn.FileExporter(f)
            game.accept(exporter)

        return filepath

    def auto_save(
        self,
        board: chess.Board,
        history: MoveHistory,
        player_color: str = "white",
        difficulty: str = "SOLDIER",
        opening_name: str = "",
        result: str = "*",
    ) -> str:
        """Auto-save to a rotating slot."""
        return self.save_game(
            board, history, player_color, difficulty,
            opening_name, result, filename="autosave.pgn",
        )

    # ── Load ────────────────────────────────────────────────────

    def load_game(self, filepath: str) -> Optional[dict]:
        """
        Load a PGN file and return game data.

        Returns a dict with:
          - headers: dict of PGN headers
          - moves: list of (san, uci, comment) tuples
          - board: the final board position
          - result: game result string
        """
        if not os.path.exists(filepath):
            return None

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                game = chess.pgn.read_game(f)

            if game is None:
                return None

            headers = dict(game.headers)
            moves = []
            board = game.board()

            node = game
            while node.variations:
                next_node = node.variation(0)
                move = next_node.move
                san = board.san(move)
                moves.append({
                    "san": san,
                    "uci": move.uci(),
                    "comment": next_node.comment or "",
                })
                board.push(move)
                node = next_node

            return {
                "headers": headers,
                "moves": moves,
                "board": board,
                "result": headers.get("Result", "*"),
            }
        except Exception:
            return None

    def list_saves(self) -> list[dict]:
        """List all saved games with metadata."""
        saves = []
        if not os.path.exists(SAVES_DIR):
            return saves

        for fname in sorted(os.listdir(SAVES_DIR), reverse=True):
            if not fname.endswith(".pgn"):
                continue
            filepath = os.path.join(SAVES_DIR, fname)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    game = chess.pgn.read_game(f)
                if game:
                    saves.append({
                        "filename": fname,
                        "filepath": filepath,
                        "date": game.headers.get("Date", "??"),
                        "white": game.headers.get("White", "??"),
                        "black": game.headers.get("Black", "??"),
                        "result": game.headers.get("Result", "*"),
                        "opening": game.headers.get("Opening", ""),
                        "modified": os.path.getmtime(filepath),
                    })
            except Exception:
                continue

        return saves

    def delete_save(self, filepath: str) -> bool:
        """Delete a saved game file."""
        try:
            if os.path.exists(filepath) and filepath.endswith(".pgn"):
                os.remove(filepath)
                return True
        except Exception:
            pass
        return False

    def export_pgn_string(
        self,
        board: chess.Board,
        history: MoveHistory,
        player_color: str = "white",
        difficulty: str = "SOLDIER",
        result: str = "*",
    ) -> str:
        """Export the game as a PGN string (for clipboard)."""
        game = chess.pgn.Game()
        game.headers["Event"] = "Chess Battle & War Strategy"
        game.headers["Date"] = datetime.now().strftime("%Y.%m.%d")
        game.headers["White"] = "Player" if player_color == "white" else f"AI ({difficulty})"
        game.headers["Black"] = f"AI ({difficulty})" if player_color == "white" else "Player"
        game.headers["Result"] = result

        node = game
        replay = chess.Board()
        for record in history.moves:
            move = chess.Move.from_uci(record.uci)
            if move in replay.legal_moves:
                node = node.add_variation(move)
                replay.push(move)

        sio = io.StringIO()
        exporter = chess.pgn.FileExporter(sio)
        game.accept(exporter)
        return sio.getvalue()
