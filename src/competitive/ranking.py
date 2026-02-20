"""
ELO rating engine — calculates rating changes after each match.

Implements the standard ELO system with:
- K-factor adjustment based on rating and games played
- Provisional rating handling for new players
- Tier assignment based on ELO thresholds
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from src.competitive.database import Database


# ─────────────────────────────────────────────────────────────────────────────
# Tier Definitions
# ─────────────────────────────────────────────────────────────────────────────
TIERS = [
    {"name": "Bronze",      "min_elo": 0,    "badge": "🥉", "color": (205, 127, 50)},
    {"name": "Silver",      "min_elo": 1100, "badge": "🥈", "color": (192, 192, 192)},
    {"name": "Gold",        "min_elo": 1400, "badge": "🥇", "color": (255, 215, 0)},
    {"name": "Platinum",    "min_elo": 1700, "badge": "💎", "color": (100, 200, 255)},
    {"name": "Diamond",     "min_elo": 2000, "badge": "👑", "color": (185, 242, 255)},
    {"name": "Grandmaster", "min_elo": 2500, "badge": "♔",  "color": (255, 80, 80)},
]


def get_tier(elo: int) -> dict[str, Any]:
    """Return the tier dict for a given ELO rating."""
    result = TIERS[0]
    for tier in TIERS:
        if elo >= tier["min_elo"]:
            result = tier
    return result


def get_tier_name(elo: int) -> str:
    return get_tier(elo)["name"]


def get_tier_badge(elo: int) -> str:
    return get_tier(elo)["badge"]


# ─────────────────────────────────────────────────────────────────────────────
# K-Factor Calculation
# ─────────────────────────────────────────────────────────────────────────────
def _k_factor(elo: int, games_played: int) -> int:
    """
    Dynamic K-factor:
    - New players (<30 games): K=40 (large swings for calibration)
    - Under 2400: K=20 (standard)
    - Over 2400: K=10 (established players change slowly)
    """
    if games_played < 30:
        return 40
    if elo < 2400:
        return 20
    return 10


# ─────────────────────────────────────────────────────────────────────────────
# ELO Calculation
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class RatingChange:
    """Result of a rating calculation."""
    old_rating: int
    new_rating: int
    change: int
    old_tier: str
    new_tier: str
    promoted: bool       # did the player move to a higher tier?
    demoted: bool        # did the player drop to a lower tier?
    new_peak: bool       # is this a new all-time high?


def calculate_elo_change(
    player_elo: int,
    opponent_elo: int,
    result: float,  # 1.0 = win, 0.5 = draw, 0.0 = loss
    player_games: int = 30,
) -> tuple[int, int]:
    """
    Calculate new ELO ratings for both player and opponent.
    Returns (player_new_elo, opponent_new_elo).
    """
    # Expected scores
    exp_player = 1.0 / (1.0 + math.pow(10.0, (opponent_elo - player_elo) / 400.0))
    exp_opponent = 1.0 - exp_player

    # K-factors
    k_player = _k_factor(player_elo, player_games)
    k_opponent = _k_factor(opponent_elo, 999)  # AI always uses low K

    # New ratings (floor at 0)
    player_new = max(0, round(player_elo + k_player * (result - exp_player)))
    opponent_new = max(0, round(opponent_elo + k_opponent * ((1.0 - result) - exp_opponent)))

    return player_new, opponent_new


class RankingEngine:
    """
    High-level ranking engine — processes match results and updates the database.
    """

    def __init__(self, db: Database | None = None):
        self.db = db or Database.get_instance()

    def process_match(
        self,
        player_name: str,
        difficulty: str,
        result: str,          # "1-0", "0-1", "1/2-1/2"
        player_color: str,    # "white" or "black"
        moves_count: int = 0,
        duration: float = 0.0,
        opening_name: str = "",
        accuracy: float | None = None,
        game_mode: str = "ranked",
        pgn_path: str = "",
    ) -> RatingChange:
        """
        Process a completed match:
        1. Look up / create player
        2. Look up AI opponent
        3. Calculate ELO change
        4. Update both ratings
        5. Record match in history
        6. Return RatingChange for display
        """
        player = self.db.get_or_create_player(player_name)
        ai = self.db.get_ai_opponent(difficulty)
        if ai is None:
            raise ValueError(f"Unknown AI difficulty: {difficulty}")

        # Determine actual score from the result and player color
        score = self._result_to_score(result, player_color)

        # Determine win/loss/draw code
        if score == 1.0:
            player_won = 1
        elif score == 0.0:
            player_won = 0
        else:
            player_won = -1

        old_player_elo = player["elo"]
        old_ai_elo = ai["elo"]
        old_tier = get_tier_name(old_player_elo)

        # Calculate new ratings
        if game_mode == "casual":
            # Casual mode: no ELO changes
            new_player_elo = old_player_elo
            new_ai_elo = old_ai_elo
        else:
            new_player_elo, new_ai_elo = calculate_elo_change(
                old_player_elo, old_ai_elo, score, player["games_played"]
            )

        elo_change = new_player_elo - old_player_elo
        new_tier = get_tier_name(new_player_elo)
        new_peak = new_player_elo > player["peak_elo"]
        peak_elo = max(player["peak_elo"], new_player_elo)

        # Update streaks
        if player_won == 1:
            new_streak = player["win_streak"] + 1
            best_streak = max(player["best_streak"], new_streak)
        else:
            new_streak = 0
            best_streak = player["best_streak"]

        # Update player record
        self.db.execute_update(
            """UPDATE players SET
                elo = ?, peak_elo = ?, tier = ?,
                games_played = games_played + 1,
                wins = wins + ?, losses = losses + ?, draws = draws + ?,
                win_streak = ?, best_streak = ?,
                total_time_played = total_time_played + ?,
                updated_at = datetime('now')
            WHERE id = ?""",
            (
                new_player_elo, peak_elo, new_tier,
                1 if player_won == 1 else 0,
                1 if player_won == 0 else 0,
                1 if player_won == -1 else 0,
                new_streak, best_streak,
                duration,
                player["id"],
            ),
        )

        # Update AI opponent record
        ai_won = 1 if player_won == 0 else (0 if player_won == 1 else -1)
        self.db.execute_update(
            """UPDATE ai_opponents SET
                elo = ?, peak_elo = MAX(peak_elo, ?),
                games_played = games_played + 1,
                wins = wins + ?, losses = losses + ?, draws = draws + ?
            WHERE id = ?""",
            (
                new_ai_elo, new_ai_elo,
                1 if ai_won == 1 else 0,
                1 if ai_won == 0 else 0,
                1 if ai_won == -1 else 0,
                ai["id"],
            ),
        )

        # Record match in history
        self.db.execute_insert(
            """INSERT INTO match_history
               (player_id, opponent_type, opponent_id, opponent_name,
                player_color, result, player_won,
                player_elo_before, player_elo_after,
                opponent_elo_before, opponent_elo_after,
                elo_change, moves_count, duration_seconds,
                opening_name, accuracy, game_mode, pgn_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                player["id"], "ai_builtin", ai["id"], ai["name"],
                player_color, result, player_won,
                old_player_elo, new_player_elo,
                old_ai_elo, new_ai_elo,
                elo_change, moves_count, duration,
                opening_name, accuracy, game_mode, pgn_path,
            ),
        )

        return RatingChange(
            old_rating=old_player_elo,
            new_rating=new_player_elo,
            change=elo_change,
            old_tier=old_tier,
            new_tier=new_tier,
            promoted=(TIERS.index(get_tier(new_player_elo)) > TIERS.index(get_tier(old_player_elo))),
            demoted=(TIERS.index(get_tier(new_player_elo)) < TIERS.index(get_tier(old_player_elo))),
            new_peak=new_peak,
        )

    @staticmethod
    def _result_to_score(result: str, player_color: str) -> float:
        """Convert PGN result string to a float score from the player's perspective."""
        if result == "1/2-1/2":
            return 0.5
        if result == "1-0":
            return 1.0 if player_color == "white" else 0.0
        if result == "0-1":
            return 1.0 if player_color == "black" else 0.0
        # Unknown result (game still in progress) — treat as draw
        return 0.5
