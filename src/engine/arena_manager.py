"""
AI Arena Manager — orchestrates external-model matches.

Handles:
  • Model registration and tracking in the database
  • Player vs External AI match flow
  • AI vs AI spectator mode
  • External model ELO tracking on the unified leaderboard
"""

from __future__ import annotations

import time
import threading
from typing import Any, Optional

import chess

from src.engine.arena_adapter import (
    ArenaAdapter, ArenaMove, ArenaModelInfo,
    get_available_adapters, create_adapter,
)
from src.competitive.database import Database
from src.competitive.ranking import calculate_elo_change


# ─────────────────────────────────────────────────────────────────────────────
# Database helper for external AI models
# ─────────────────────────────────────────────────────────────────────────────

_ARENA_SCHEMA = """
CREATE TABLE IF NOT EXISTS arena_models (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    model_id        TEXT    NOT NULL UNIQUE,
    display_name    TEXT    NOT NULL,
    provider        TEXT    NOT NULL,
    elo             INTEGER NOT NULL DEFAULT 1500,
    peak_elo        INTEGER NOT NULL DEFAULT 1500,
    games_played    INTEGER NOT NULL DEFAULT 0,
    wins            INTEGER NOT NULL DEFAULT 0,
    losses          INTEGER NOT NULL DEFAULT 0,
    draws           INTEGER NOT NULL DEFAULT 0,
    last_played     TEXT,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_arena_models_elo ON arena_models(elo DESC);
"""


class ArenaManager:
    """Central manager for external AI arena matches."""

    def __init__(self, db: Database | None = None):
        self.db = db or Database.get_instance()
        self._ensure_table()
        self._adapters: dict[str, ArenaAdapter] = {}
        self._active_match: Optional[ArenaMatch] = None

    def _ensure_table(self) -> None:
        with self.db.connect() as conn:
            conn.executescript(_ARENA_SCHEMA)

    # ── Model Management ────────────────────────────────────────

    def register_model(self, adapter: ArenaAdapter) -> dict[str, Any]:
        """
        Register an external model in the database (if not already present)
        and store the adapter instance.
        """
        info = adapter.get_info()
        self._adapters[info.model_id] = adapter

        # Check if already in DB
        rows = self.db.execute(
            "SELECT * FROM arena_models WHERE model_id = ?", (info.model_id,)
        )
        if rows:
            return dict(rows[0])

        # Insert new model
        self.db.execute_insert(
            """INSERT INTO arena_models
               (model_id, display_name, provider, elo, peak_elo)
               VALUES (?, ?, ?, ?, ?)""",
            (info.model_id, info.display_name, info.provider,
             info.default_elo, info.default_elo),
        )
        rows = self.db.execute(
            "SELECT * FROM arena_models WHERE model_id = ?", (info.model_id,)
        )
        return dict(rows[0])

    def get_model_profile(self, model_id: str) -> dict[str, Any] | None:
        """Get a model's arena profile from the database."""
        rows = self.db.execute(
            "SELECT * FROM arena_models WHERE model_id = ?", (model_id,)
        )
        return dict(rows[0]) if rows else None

    def get_all_models(self) -> list[dict[str, Any]]:
        """Get all registered arena models sorted by ELO desc."""
        rows = self.db.execute(
            "SELECT * FROM arena_models ORDER BY elo DESC"
        )
        return [dict(r) for r in rows]

    def get_adapter(self, model_id: str) -> ArenaAdapter | None:
        """Get a configured adapter instance by model ID."""
        return self._adapters.get(model_id)

    def get_registered_adapters(self) -> dict[str, ArenaAdapter]:
        """Return all currently loaded adapter instances."""
        return dict(self._adapters)

    # ── ELO Tracking ────────────────────────────────────────────

    def update_model_elo(
        self, model_id: str, new_elo: int, won: bool | None = None
    ) -> None:
        """Update a model's ELO and win/loss/draw counters."""
        model = self.get_model_profile(model_id)
        if not model:
            return

        peak = max(model["peak_elo"], new_elo)

        updates = [
            "elo = ?", "peak_elo = ?", "games_played = games_played + 1",
            "last_played = datetime('now')",
        ]
        params: list[Any] = [new_elo, peak]

        if won is True:
            updates.append("wins = wins + 1")
        elif won is False:
            updates.append("losses = losses + 1")
        else:
            updates.append("draws = draws + 1")

        params.append(model_id)
        sql = f"UPDATE arena_models SET {', '.join(updates)} WHERE model_id = ?"
        self.db.execute_update(sql, tuple(params))

    def get_unified_leaderboard_entries(self) -> list[dict[str, Any]]:
        """
        Return arena models formatted for the unified leaderboard.
        Each entry has: name, elo, type, games_played, etc.
        """
        models = self.get_all_models()
        entries = []
        for m in models:
            entries.append({
                "name": f"🤖 {m['display_name']}",
                "elo": m["elo"],
                "type": "ai_external",
                "games_played": m["games_played"],
                "wins": m["wins"],
                "losses": m["losses"],
                "draws": m["draws"],
                "model_id": m["model_id"],
                "provider": m["provider"],
            })
        return entries

    # ── Match Orchestration ─────────────────────────────────────

    def create_match(
        self,
        adapter: ArenaAdapter,
        player_color: str = "white",
        mode: str = "player_vs_ai",
        second_adapter: ArenaAdapter | None = None,
    ) -> ArenaMatch:
        """
        Create a new arena match.
        mode: "player_vs_ai" or "ai_vs_ai"
        """
        match = ArenaMatch(
            adapter=adapter,
            player_color=player_color,
            mode=mode,
            second_adapter=second_adapter,
            manager=self,
        )
        self._active_match = match
        return match

    @property
    def active_match(self) -> Optional[ArenaMatch]:
        return self._active_match

    def record_arena_result(
        self,
        model_id: str,
        player_name: str,
        player_elo: int,
        model_elo: int,
        score: float,  # 1.0=player win, 0.0=player loss, 0.5=draw
    ) -> dict[str, Any]:
        """
        Record a match result between a player and an external model.
        Updates both player's and model's ELO.
        Returns dict with ELO changes.
        """
        k_factor = 32
        new_player_elo, new_model_elo = calculate_elo_change(
            player_elo, model_elo, score, k_factor
        )

        # Update model in arena_models table
        model_won = score == 0.0
        model_drew = score == 0.5
        self.update_model_elo(
            model_id, new_model_elo,
            won=model_won if not model_drew else None,
        )

        return {
            "player_elo_before": player_elo,
            "player_elo_after": new_player_elo,
            "model_elo_before": model_elo,
            "model_elo_after": new_model_elo,
            "player_change": new_player_elo - player_elo,
            "model_change": new_model_elo - model_elo,
        }


# ─────────────────────────────────────────────────────────────────────────────
# Arena Match
# ─────────────────────────────────────────────────────────────────────────────

class ArenaMatch:
    """
    Represents a single arena match.

    For player_vs_ai mode: the external model is the opponent.
    For ai_vs_ai mode: two external models play each other.
    """

    def __init__(
        self,
        adapter: ArenaAdapter,
        player_color: str = "white",
        mode: str = "player_vs_ai",
        second_adapter: ArenaAdapter | None = None,
        manager: ArenaManager | None = None,
    ):
        self.adapter = adapter
        self.second_adapter = second_adapter
        self.player_color = player_color
        self.mode = mode
        self.manager = manager

        self.board = chess.Board()
        self.move_history: list[str] = []
        self.last_move_explanation: str = ""
        self.thinking = False
        self._move_callback: Any = None

    @property
    def model_info(self) -> ArenaModelInfo:
        return self.adapter.get_info()

    def request_ai_move(self, callback: Any = None) -> None:
        """
        Request a move from the external AI (non-blocking).
        The callback(ArenaMove) is called when the move is ready.
        """
        self.thinking = True
        self._move_callback = callback

        def _worker():
            result = self.adapter.get_move(self.board, self.move_history)
            self.thinking = False
            self.last_move_explanation = result.explanation
            if callback:
                callback(result)

        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()

    def request_ai_move_sync(self) -> ArenaMove:
        """Blocking version — request a move and wait for it."""
        self.thinking = True
        result = self.adapter.get_move(self.board, self.move_history)
        self.thinking = False
        self.last_move_explanation = result.explanation
        return result

    def apply_move(self, uci_move: str) -> bool:
        """Apply a UCI move to the match board. Returns True if valid."""
        try:
            move = chess.Move.from_uci(uci_move)
            if move in self.board.legal_moves:
                self.board.push(move)
                self.move_history.append(uci_move)
                return True
        except (ValueError, chess.InvalidMoveError):
            pass
        return False

    @property
    def is_game_over(self) -> bool:
        return self.board.is_game_over()

    @property
    def result(self) -> str:
        """Get game result string."""
        if not self.board.is_game_over():
            return "*"
        return self.board.result()

    def get_winner(self) -> str:
        """Return 'white', 'black', or 'draw'."""
        r = self.result
        if r == "1-0":
            return "white"
        elif r == "0-1":
            return "black"
        return "draw"
