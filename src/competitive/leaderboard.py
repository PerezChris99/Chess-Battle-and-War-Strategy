"""
Leaderboard system — queries and formats ranking data for display.

Provides sorted rankings, filtering, and combined player+AI leaderboards.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.competitive.database import Database
from src.competitive.ranking import get_tier_name, get_tier_badge


@dataclass
class LeaderboardEntry:
    """Single entry on the leaderboard."""
    rank: int
    name: str
    elo: int
    tier: str
    badge: str
    games_played: int
    wins: int
    losses: int
    draws: int
    win_rate: float          # 0.0–1.0
    best_streak: int
    is_player: bool          # True = human, False = AI
    is_current_player: bool  # Highlighted in the UI


class Leaderboard:
    """Builds and queries the unified leaderboard."""

    def __init__(self, db: Database | None = None):
        self.db = db or Database.get_instance()

    def get_unified_leaderboard(self, player_name: str = "Player") -> list[LeaderboardEntry]:
        """
        Build a unified leaderboard containing the player and all AI opponents,
        sorted by ELO descending.
        """
        entries: list[LeaderboardEntry] = []

        # Player(s)
        player_rows = self.db.execute(
            "SELECT * FROM players ORDER BY elo DESC"
        )
        for row in player_rows:
            p = dict(row)
            total = p["wins"] + p["losses"] + p["draws"]
            entries.append(LeaderboardEntry(
                rank=0,  # assigned after sorting
                name=p["name"],
                elo=p["elo"],
                tier=get_tier_name(p["elo"]),
                badge=get_tier_badge(p["elo"]),
                games_played=p["games_played"],
                wins=p["wins"],
                losses=p["losses"],
                draws=p["draws"],
                win_rate=p["wins"] / total if total > 0 else 0.0,
                best_streak=p["best_streak"],
                is_player=True,
                is_current_player=(p["name"] == player_name),
            ))

        # AI opponents
        ai_rows = self.db.execute(
            "SELECT * FROM ai_opponents ORDER BY elo DESC"
        )
        for row in ai_rows:
            a = dict(row)
            total = a["wins"] + a["losses"] + a["draws"]
            entries.append(LeaderboardEntry(
                rank=0,
                name=f"⚔ {a['name']}",
                elo=a["elo"],
                tier=get_tier_name(a["elo"]),
                badge=get_tier_badge(a["elo"]),
                games_played=a["games_played"],
                wins=a["wins"],
                losses=a["losses"],
                draws=a["draws"],
                win_rate=a["wins"] / total if total > 0 else 0.0,
                best_streak=0,
                is_player=False,
                is_current_player=False,
            ))

        # Sort by ELO descending, assign ranks
        entries.sort(key=lambda e: e.elo, reverse=True)
        for i, entry in enumerate(entries):
            entry.rank = i + 1

        return entries

    def get_player_rank(self, player_name: str = "Player") -> int | None:
        """Return the 1-based rank of a player on the unified leaderboard."""
        board = self.get_unified_leaderboard(player_name)
        for entry in board:
            if entry.is_current_player:
                return entry.rank
        return None

    def get_recent_matches(
        self, player_name: str = "Player", limit: int = 20
    ) -> list[dict[str, Any]]:
        """Return the most recent matches for a player."""
        player = self.db.get_or_create_player(player_name)
        rows = self.db.execute(
            """SELECT * FROM match_history
               WHERE player_id = ?
               ORDER BY played_at DESC
               LIMIT ?""",
            (player["id"], limit),
        )
        return [dict(r) for r in rows]

    def get_head_to_head(
        self, player_name: str, opponent_difficulty: str
    ) -> dict[str, int]:
        """Return win/loss/draw record vs a specific AI opponent."""
        player = self.db.get_or_create_player(player_name)
        ai = self.db.get_ai_opponent(opponent_difficulty)
        if not ai:
            return {"wins": 0, "losses": 0, "draws": 0}

        rows = self.db.execute(
            """SELECT player_won, COUNT(*) as cnt
               FROM match_history
               WHERE player_id = ? AND opponent_id = ? AND opponent_type = 'ai_builtin'
               GROUP BY player_won""",
            (player["id"], ai["id"]),
        )
        result = {"wins": 0, "losses": 0, "draws": 0}
        for row in rows:
            r = dict(row)
            if r["player_won"] == 1:
                result["wins"] = r["cnt"]
            elif r["player_won"] == 0:
                result["losses"] = r["cnt"]
            else:
                result["draws"] = r["cnt"]
        return result

    def get_player_summary(self, player_name: str = "Player") -> dict[str, Any]:
        """Get a comprehensive summary of a player's competitive profile."""
        player = self.db.get_or_create_player(player_name)
        rank = self.get_player_rank(player_name)

        # Average accuracy from recent games
        rows = self.db.execute(
            """SELECT AVG(accuracy) as avg_acc
               FROM match_history
               WHERE player_id = ? AND accuracy IS NOT NULL""",
            (player["id"],),
        )
        avg_accuracy = dict(rows[0])["avg_acc"] if rows and rows[0]["avg_acc"] else None

        # Best win (highest ELO opponent beaten)
        rows = self.db.execute(
            """SELECT opponent_name, opponent_elo_before
               FROM match_history
               WHERE player_id = ? AND player_won = 1
               ORDER BY opponent_elo_before DESC LIMIT 1""",
            (player["id"],),
        )
        best_win = dict(rows[0]) if rows else None

        return {
            "name": player["name"],
            "elo": player["elo"],
            "peak_elo": player["peak_elo"],
            "tier": get_tier_name(player["elo"]),
            "badge": get_tier_badge(player["elo"]),
            "rank": rank,
            "games_played": player["games_played"],
            "wins": player["wins"],
            "losses": player["losses"],
            "draws": player["draws"],
            "win_rate": player["wins"] / max(1, player["games_played"]),
            "win_streak": player["win_streak"],
            "best_streak": player["best_streak"],
            "avg_accuracy": avg_accuracy,
            "best_win": best_win,
            "total_time_played": player["total_time_played"],
        }
