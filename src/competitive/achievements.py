"""
Achievement definitions and tracking engine.

Defines 30+ achievements across 10 categories, detects unlocks in real-time,
and persists earned achievements in the database.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.competitive.database import Database


# ─────────────────────────────────────────────────────────────────────────────
# Achievement Definitions
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class AchievementDef:
    """Definition of a single achievement."""
    id: str                # unique key, e.g. "first_blood"
    name: str              # display name
    description: str       # how to earn it
    category: str          # category grouping
    icon: str              # emoji icon
    rarity: str            # "common", "uncommon", "rare", "epic", "legendary"
    stat_key: str | None   # which stat to check (or None for custom logic)
    threshold: float       # stat value required to unlock
    prize_id: str | None   # prize awarded on unlock (if any)


# All achievement definitions — 30+ across 10 categories
ACHIEVEMENTS: list[AchievementDef] = [
    # ── First Blood ──
    AchievementDef("first_win", "First Blood", "Win your first game", "First Blood", "⚔", "common", "total_wins", 1, "title_warrior"),
    AchievementDef("play_10", "Veteran", "Play 10 games", "First Blood", "🎖", "common", "total_games", 10, None),
    AchievementDef("play_50", "War Hardened", "Play 50 games", "First Blood", "🏅", "uncommon", "total_games", 50, "badge_shield"),
    AchievementDef("play_100", "Centurion", "Play 100 games", "First Blood", "🏛", "rare", "total_games", 100, "medal_bronze_star"),

    # ── Rank Climber ──
    AchievementDef("reach_silver", "Silver Ascension", "Reach Silver tier", "Rank Climber", "🥈", "common", None, 0, "title_silver_knight"),
    AchievementDef("reach_gold", "Golden Commander", "Reach Gold tier", "Rank Climber", "🥇", "uncommon", None, 0, "badge_gold_crown"),
    AchievementDef("reach_platinum", "Platinum Marshal", "Reach Platinum tier", "Rank Climber", "💎", "rare", None, 0, "medal_silver_eagle"),
    AchievementDef("reach_diamond", "Diamond Sovereign", "Reach Diamond tier", "Rank Climber", "👑", "epic", None, 0, "banner_royal_court"),
    AchievementDef("reach_grandmaster", "Grandmaster of War", "Reach Grandmaster tier", "Rank Climber", "♔", "legendary", None, 0, "title_grandmaster"),

    # ── Giant Slayer ──
    AchievementDef("beat_soldier", "Soldier Down", "Beat the Soldier AI", "Giant Slayer", "⚔", "common", None, 0, None),
    AchievementDef("beat_captain", "Captain Conquered", "Beat the Captain AI", "Giant Slayer", "🗡", "uncommon", None, 0, "badge_crossed_swords"),
    AchievementDef("beat_general", "Generalissimo", "Beat the General AI", "Giant Slayer", "⚔", "rare", None, 0, "medal_gold_crown"),
    AchievementDef("beat_magnus", "Magnus Rival", "Beat Magnus Mode AI", "Giant Slayer", "🔥", "legendary", None, 0, "title_magnus_rival"),

    # ── Tactical Master ──
    AchievementDef("captures_50", "Battlefield Collector", "Capture 50 pieces total", "Tactical Master", "🎯", "common", "total_captures", 50, None),
    AchievementDef("captures_200", "Piece Hunter", "Capture 200 pieces total", "Tactical Master", "🏹", "uncommon", "total_captures", 200, "badge_flame"),
    AchievementDef("checks_25", "Check Artist", "Deliver 25 checks total", "Tactical Master", "♚", "common", "total_checks", 25, None),
    AchievementDef("checks_100", "Check Master", "Deliver 100 checks total", "Tactical Master", "🎭", "rare", "total_checks", 100, "medal_diamond_scepter"),

    # ── Endgame Specialist ──
    AchievementDef("win_5_endgames", "Endgame Tactician", "Win 5 games with ≤10 pieces on board", "Endgame Specialist", "♟", "uncommon", "endgame_wins", 5, None),

    # ── Speed Demon ──
    AchievementDef("fast_win", "Lightning Strike", "Win a game in under 20 moves", "Speed Demon", "⚡", "rare", "fast_wins", 1, "badge_lightning"),

    # ── Streak Warrior ──
    AchievementDef("streak_3", "Hat Trick", "Win 3 games in a row", "Streak Warrior", "🔥", "common", None, 0, None),
    AchievementDef("streak_5", "Unstoppable", "Win 5 games in a row", "Streak Warrior", "💪", "uncommon", None, 0, "badge_fire"),
    AchievementDef("streak_10", "War Machine", "Win 10 games in a row", "Streak Warrior", "🏆", "epic", None, 0, "title_war_machine"),

    # ── War Collector ──
    AchievementDef("own_5_prizes", "Collector", "Own 5 prizes", "War Collector", "📦", "common", None, 0, None),
    AchievementDef("own_15_prizes", "Treasure Hoard", "Own 15 prizes", "War Collector", "💰", "uncommon", None, 0, None),
    AchievementDef("own_25_prizes", "War Chest", "Own 25 prizes", "War Collector", "👑", "rare", None, 0, "banner_midnight_siege"),

    # ── Scholar ──
    AchievementDef("complete_lessons", "War Scholar", "Complete all tutorial lessons", "Scholar", "📖", "uncommon", "lessons_completed", 12, "title_scholar"),

    # ── Accuracy ──
    AchievementDef("accuracy_80", "Sharp Mind", "Achieve 80%+ accuracy in a game", "Accuracy", "🎯", "common", "best_accuracy", 80, None),
    AchievementDef("accuracy_90", "Precision Strike", "Achieve 90%+ accuracy in a game", "Accuracy", "🔬", "rare", "best_accuracy", 90, "badge_precision"),
    AchievementDef("accuracy_95", "Perfection", "Achieve 95%+ accuracy in a game", "Accuracy", "💎", "epic", "best_accuracy", 95, "medal_perfection"),

    # ── Castle Master ──
    AchievementDef("castle_50", "Fortress Builder", "Castle in 50% of your games", "Castle Master", "🏰", "uncommon", None, 0, "badge_fortress"),
]

ACHIEVEMENT_MAP: dict[str, AchievementDef] = {a.id: a for a in ACHIEVEMENTS}
CATEGORIES: list[str] = sorted(set(a.category for a in ACHIEVEMENTS))

# DB schema additions for achievements
_ACHIEVEMENT_SCHEMA = """
CREATE TABLE IF NOT EXISTS player_achievements (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id       INTEGER NOT NULL REFERENCES players(id),
    achievement_id  TEXT    NOT NULL,
    unlocked_at     TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE(player_id, achievement_id)
);
CREATE INDEX IF NOT EXISTS idx_achievements_player
    ON player_achievements(player_id);
"""


class AchievementEngine:
    """Detects and tracks achievement unlocks."""

    def __init__(self, db: Database | None = None):
        self.db = db or Database.get_instance()
        self._ensure_table()
        self._recent_unlocks: list[AchievementDef] = []

    def _ensure_table(self) -> None:
        """Create the achievements table if it doesn't exist."""
        with self.db.connect() as conn:
            conn.executescript(_ACHIEVEMENT_SCHEMA)

    @property
    def recent_unlocks(self) -> list[AchievementDef]:
        """Return achievements unlocked in the last check, then clear."""
        unlocks = self._recent_unlocks.copy()
        self._recent_unlocks.clear()
        return unlocks

    def get_earned(self, player_name: str) -> list[str]:
        """Return list of achievement IDs earned by the player."""
        player = self.db.get_or_create_player(player_name)
        rows = self.db.execute(
            "SELECT achievement_id FROM player_achievements WHERE player_id = ?",
            (player["id"],),
        )
        return [r["achievement_id"] for r in rows]

    def get_earned_count(self, player_name: str) -> int:
        return len(self.get_earned(player_name))

    def get_progress(self, player_name: str) -> list[dict[str, Any]]:
        """
        Return all achievements with their progress.
        Each dict: {achievement, earned, progress_pct}
        """
        earned_ids = set(self.get_earned(player_name))
        stats = self._get_player_stats(player_name)
        player = self.db.get_or_create_player(player_name)

        results = []
        for ach in ACHIEVEMENTS:
            earned = ach.id in earned_ids
            progress = self._calc_progress(ach, stats, player)
            results.append({
                "achievement": ach,
                "earned": earned,
                "progress_pct": 100.0 if earned else min(99.9, progress),
            })
        return results

    def check_unlocks(
        self,
        player_name: str,
        match_result: dict[str, Any] | None = None,
    ) -> list[AchievementDef]:
        """
        Check all un-earned achievements and unlock any that are now met.
        Returns list of newly unlocked achievements.

        match_result: optional dict with keys like 'difficulty', 'player_won',
                      'rating_change', etc. for context-sensitive checks.
        """
        earned_ids = set(self.get_earned(player_name))
        stats = self._get_player_stats(player_name)
        player = self.db.get_or_create_player(player_name)
        newly_unlocked: list[AchievementDef] = []

        for ach in ACHIEVEMENTS:
            if ach.id in earned_ids:
                continue
            if self._is_unlocked(ach, stats, player, match_result):
                self._award(player["id"], ach.id)
                newly_unlocked.append(ach)
                earned_ids.add(ach.id)

        self._recent_unlocks = newly_unlocked
        return newly_unlocked

    # ── Private ─────────────────────────────────────────────────

    def _get_player_stats(self, player_name: str) -> dict[str, float]:
        """Get all stats as a dict."""
        player = self.db.get_or_create_player(player_name)
        rows = self.db.execute(
            "SELECT stat_key, stat_value FROM player_stats WHERE player_id = ?",
            (player["id"],),
        )
        return {r["stat_key"]: float(r["stat_value"]) for r in rows}

    def _is_unlocked(
        self,
        ach: AchievementDef,
        stats: dict[str, float],
        player: dict[str, Any],
        match_result: dict[str, Any] | None,
    ) -> bool:
        """Check if a specific achievement is now unlocked."""
        # Stat-based checks
        if ach.stat_key:
            return stats.get(ach.stat_key, 0) >= ach.threshold

        # Custom logic checks by ID
        mr = match_result or {}

        # Tier-based
        if ach.id == "reach_silver":
            return player["elo"] >= 1100
        if ach.id == "reach_gold":
            return player["elo"] >= 1400
        if ach.id == "reach_platinum":
            return player["elo"] >= 1700
        if ach.id == "reach_diamond":
            return player["elo"] >= 2000
        if ach.id == "reach_grandmaster":
            return player["elo"] >= 2500

        # Giant slayer
        if ach.id == "beat_soldier":
            return mr.get("difficulty") == "SOLDIER" and mr.get("player_won", False)
        if ach.id == "beat_captain":
            return mr.get("difficulty") == "CAPTAIN" and mr.get("player_won", False)
        if ach.id == "beat_general":
            return mr.get("difficulty") == "GENERAL" and mr.get("player_won", False)
        if ach.id == "beat_magnus":
            return mr.get("difficulty") == "MAGNUS" and mr.get("player_won", False)

        # Streak
        if ach.id == "streak_3":
            return player["best_streak"] >= 3
        if ach.id == "streak_5":
            return player["best_streak"] >= 5
        if ach.id == "streak_10":
            return player["best_streak"] >= 10

        # Collection
        if ach.id in ("own_5_prizes", "own_15_prizes", "own_25_prizes"):
            prize_count = self._count_prizes(player["id"])
            thresholds = {"own_5_prizes": 5, "own_15_prizes": 15, "own_25_prizes": 25}
            return prize_count >= thresholds.get(ach.id, 999)

        # Castle master
        if ach.id == "castle_50":
            games = stats.get("total_games", 0)
            castled = stats.get("games_castled", 0)
            return games >= 10 and (castled / games) >= 0.5

        return False

    def _calc_progress(
        self,
        ach: AchievementDef,
        stats: dict[str, float],
        player: dict[str, Any],
    ) -> float:
        """Calculate progress percentage (0-100) for an achievement."""
        if ach.stat_key and ach.threshold > 0:
            current = stats.get(ach.stat_key, 0)
            return min(100.0, (current / ach.threshold) * 100)

        # Custom progress
        if ach.id == "reach_silver":
            return min(100, player["elo"] / 1100 * 100)
        if ach.id == "reach_gold":
            return min(100, player["elo"] / 1400 * 100)

        if ach.id in ("streak_3", "streak_5", "streak_10"):
            targets = {"streak_3": 3, "streak_5": 5, "streak_10": 10}
            return min(100, player["best_streak"] / targets[ach.id] * 100)

        return 0.0

    def _award(self, player_id: int, achievement_id: str) -> None:
        """Insert an achievement record."""
        self.db.execute_insert(
            """INSERT OR IGNORE INTO player_achievements
               (player_id, achievement_id) VALUES (?, ?)""",
            (player_id, achievement_id),
        )

    def _count_prizes(self, player_id: int) -> int:
        """Count prizes owned by player (requires prizes table)."""
        try:
            rows = self.db.execute(
                "SELECT COUNT(*) as cnt FROM player_prizes WHERE player_id = ?",
                (player_id,),
            )
            return int(rows[0]["cnt"]) if rows else 0
        except Exception:
            return 0
