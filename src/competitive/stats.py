"""
Player & AI statistics tracker — records detailed gameplay stats.

Tracks aggregate statistics like total captures, checks, accuracy, etc.
Uses the player_stats table with key-value pairs for flexibility.
"""

from __future__ import annotations

from typing import Any

from src.competitive.database import Database


class StatsTracker:
    """Tracks and updates player statistics in the database."""

    def __init__(self, db: Database | None = None):
        self.db = db or Database.get_instance()

    def increment_stat(self, player_name: str, stat_key: str, amount: float = 1.0) -> None:
        """Add to a cumulative stat (creates if not exists)."""
        player = self.db.get_or_create_player(player_name)
        self.db.execute(
            """INSERT INTO player_stats (player_id, stat_key, stat_value)
               VALUES (?, ?, ?)
               ON CONFLICT(player_id, stat_key)
               DO UPDATE SET stat_value = stat_value + ?, updated_at = datetime('now')""",
            (player["id"], stat_key, amount, amount),
        )

    def set_stat(self, player_name: str, stat_key: str, value: float) -> None:
        """Set a stat to an absolute value."""
        player = self.db.get_or_create_player(player_name)
        self.db.execute(
            """INSERT INTO player_stats (player_id, stat_key, stat_value)
               VALUES (?, ?, ?)
               ON CONFLICT(player_id, stat_key)
               DO UPDATE SET stat_value = ?, updated_at = datetime('now')""",
            (player["id"], stat_key, value, value),
        )

    def get_stat(self, player_name: str, stat_key: str) -> float:
        """Get a single stat value (returns 0.0 if not set)."""
        player = self.db.get_or_create_player(player_name)
        rows = self.db.execute(
            "SELECT stat_value FROM player_stats WHERE player_id = ? AND stat_key = ?",
            (player["id"], stat_key),
        )
        return float(rows[0]["stat_value"]) if rows else 0.0

    def get_all_stats(self, player_name: str) -> dict[str, float]:
        """Get all stats for a player as a dict."""
        player = self.db.get_or_create_player(player_name)
        rows = self.db.execute(
            "SELECT stat_key, stat_value FROM player_stats WHERE player_id = ?",
            (player["id"],),
        )
        return {r["stat_key"]: float(r["stat_value"]) for r in rows}

    def record_game_stats(
        self,
        player_name: str,
        moves_count: int,
        captures: int,
        checks: int,
        castled: bool,
        accuracy: float | None,
        won: bool,
        duration: float,
    ) -> None:
        """Record stats from a single completed game."""
        self.increment_stat(player_name, "total_moves", moves_count)
        self.increment_stat(player_name, "total_captures", captures)
        self.increment_stat(player_name, "total_checks", checks)
        self.increment_stat(player_name, "total_games", 1)
        self.increment_stat(player_name, "total_time", duration)

        if castled:
            self.increment_stat(player_name, "games_castled", 1)
        if won:
            self.increment_stat(player_name, "total_wins", 1)

        if accuracy is not None:
            # Running average: (old_avg * old_count + new_val) / new_count
            old_count = self.get_stat(player_name, "accuracy_count")
            old_avg = self.get_stat(player_name, "avg_accuracy")
            new_count = old_count + 1
            new_avg = (old_avg * old_count + accuracy) / new_count
            self.set_stat(player_name, "avg_accuracy", new_avg)
            self.set_stat(player_name, "accuracy_count", new_count)

        # Track best accuracy
        best = self.get_stat(player_name, "best_accuracy")
        if accuracy is not None and accuracy > best:
            self.set_stat(player_name, "best_accuracy", accuracy)

    def get_display_stats(self, player_name: str) -> list[tuple[str, str]]:
        """
        Return a list of (label, value) tuples ready for UI display.
        """
        stats = self.get_all_stats(player_name)

        total_games = int(stats.get("total_games", 0))
        total_wins = int(stats.get("total_wins", 0))
        total_moves = int(stats.get("total_moves", 0))
        total_captures = int(stats.get("total_captures", 0))
        total_checks = int(stats.get("total_checks", 0))
        games_castled = int(stats.get("games_castled", 0))
        avg_accuracy = stats.get("avg_accuracy", 0)
        best_accuracy = stats.get("best_accuracy", 0)
        total_time = stats.get("total_time", 0)

        avg_moves = total_moves / total_games if total_games > 0 else 0
        castle_rate = games_castled / total_games * 100 if total_games > 0 else 0
        hours = total_time / 3600

        return [
            ("Games Played", str(total_games)),
            ("Total Wins", str(total_wins)),
            ("Total Moves", str(total_moves)),
            ("Avg Moves/Game", f"{avg_moves:.1f}"),
            ("Total Captures", str(total_captures)),
            ("Total Checks", str(total_checks)),
            ("Castle Rate", f"{castle_rate:.0f}%"),
            ("Avg Accuracy", f"{avg_accuracy:.1f}%" if avg_accuracy > 0 else "—"),
            ("Best Accuracy", f"{best_accuracy:.1f}%" if best_accuracy > 0 else "—"),
            ("Time Played", f"{hours:.1f}h"),
        ]
