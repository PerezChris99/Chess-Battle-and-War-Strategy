"""
Prize system — catalog, ownership, wagering.

Prize types: Titles, Badges, War Medals, Banners.
Modes: Casual earning (progressive), Ranked earning (milestones),
       War Wager (stake & win/lose prizes in head-to-head).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.competitive.database import Database


# ─────────────────────────────────────────────────────────────────────────────
# Prize Definitions
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class PrizeDef:
    """Definition of a prize."""
    id: str               # unique key
    name: str             # display name
    description: str      # how it looks / what it represents
    prize_type: str       # "title", "badge", "medal", "banner"
    rarity: str           # "common", "uncommon", "rare", "epic", "legendary"
    icon: str             # emoji icon
    wagerable: bool       # can this prize be wagered?


# Full prize catalog
PRIZES: list[PrizeDef] = [
    # Titles (displayed next to player name)
    PrizeDef("title_warrior",     "War Veteran",       "A seasoned battle commander",           "title", "common",    "⚔",  True),
    PrizeDef("title_silver_knight", "Silver Knight",   "Knighted for reaching Silver tier",     "title", "uncommon",  "🥈", True),
    PrizeDef("title_scholar",     "War Scholar",       "Master of military theory",             "title", "uncommon",  "📖", True),
    PrizeDef("title_war_machine", "War Machine",       "An unstoppable force of destruction",   "title", "epic",      "🏆", True),
    PrizeDef("title_magnus_rival", "Magnus Rival",     "The one who challenged the Supreme Commander", "title", "legendary", "🔥", False),
    PrizeDef("title_grandmaster", "Grandmaster of War", "Supreme military strategist",          "title", "legendary", "♔",  False),
    PrizeDef("title_tactical_genius", "Tactical Genius", "Master of battlefield tactics",       "title", "rare",      "🧠", True),

    # Badges (visual icons in leaderboard)
    PrizeDef("badge_crossed_swords", "Crossed Swords",  "⚔️ twin blades of victory",           "badge", "uncommon",  "⚔️", True),
    PrizeDef("badge_shield",       "Shield of Honor",   "🛡️ defender of the realm",            "badge", "common",    "🛡️", True),
    PrizeDef("badge_flame",        "Flame of Victory",  "🔥 burns bright with triumph",        "badge", "uncommon",  "🔥", True),
    PrizeDef("badge_gold_crown",   "Golden Crown",      "👑 mark of royalty",                  "badge", "rare",      "👑", True),
    PrizeDef("badge_lightning",    "Lightning Bolt",    "⚡ speed and precision",               "badge", "rare",      "⚡", True),
    PrizeDef("badge_precision",    "Precision Eye",     "🔬 sees every detail on the board",   "badge", "rare",      "🔬", True),
    PrizeDef("badge_fire",         "Eternal Flame",     "💪 never extinguished",                "badge", "uncommon",  "💪", True),
    PrizeDef("badge_fortress",     "Fortress Badge",    "🏰 impenetrable defense",             "badge", "uncommon",  "🏰", True),

    # War Medals (rare collectibles)
    PrizeDef("medal_bronze_star",    "Bronze Star",       "For distinguished service in battle", "medal", "common",    "⭐", True),
    PrizeDef("medal_silver_eagle",   "Silver Eagle",      "Soars above the battlefield",         "medal", "rare",      "🦅", True),
    PrizeDef("medal_gold_crown",     "Gold Crown Medal",  "Highest honor of military command",   "medal", "epic",      "👑", True),
    PrizeDef("medal_diamond_scepter", "Diamond Scepter",  "Symbol of absolute tactical mastery", "medal", "epic",      "💎", True),
    PrizeDef("medal_perfection",     "Medal of Perfection", "For achieving near-perfect play",   "medal", "legendary", "🌟", False),

    # Banners (profile backgrounds)
    PrizeDef("banner_battlefield_dawn", "Battlefield Dawn",  "The calm before the storm",       "banner", "uncommon",  "🌅", True),
    PrizeDef("banner_midnight_siege",   "Midnight Siege",    "Under cover of darkness",          "banner", "rare",      "🌙", True),
    PrizeDef("banner_royal_court",      "Royal Court",       "Where kings make their moves",     "banner", "epic",      "🏰", True),
]

PRIZE_MAP: dict[str, PrizeDef] = {p.id: p for p in PRIZES}
PRIZE_TYPES: list[str] = sorted(set(p.prize_type for p in PRIZES))
RARITY_ORDER = {"common": 0, "uncommon": 1, "rare": 2, "epic": 3, "legendary": 4}


# DB schema for prizes
_PRIZE_SCHEMA = """
CREATE TABLE IF NOT EXISTS player_prizes (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id   INTEGER NOT NULL REFERENCES players(id),
    prize_id    TEXT    NOT NULL,
    source      TEXT    NOT NULL DEFAULT 'achievement',  -- 'achievement', 'wager', 'milestone'
    awarded_at  TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE(player_id, prize_id)
);

CREATE TABLE IF NOT EXISTS active_wagers (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id       INTEGER NOT NULL REFERENCES players(id),
    prize_id        TEXT    NOT NULL,
    opponent_type   TEXT    NOT NULL,  -- 'ai_builtin'
    opponent_id     INTEGER,
    status          TEXT    NOT NULL DEFAULT 'pending',  -- 'pending', 'won', 'lost'
    created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_prizes_player ON player_prizes(player_id);
CREATE INDEX IF NOT EXISTS idx_wagers_player ON active_wagers(player_id);
"""


class PrizeManager:
    """Manages prize ownership, awarding, and wagering."""

    def __init__(self, db: Database | None = None):
        self.db = db or Database.get_instance()
        self._ensure_table()

    def _ensure_table(self) -> None:
        with self.db.connect() as conn:
            conn.executescript(_PRIZE_SCHEMA)

    # ── Ownership ───────────────────────────────────────────────

    def get_owned_prizes(self, player_name: str) -> list[PrizeDef]:
        """Return list of prize definitions that the player owns."""
        player = self.db.get_or_create_player(player_name)
        rows = self.db.execute(
            "SELECT prize_id FROM player_prizes WHERE player_id = ?",
            (player["id"],),
        )
        owned_ids = {r["prize_id"] for r in rows}
        return [p for p in PRIZES if p.id in owned_ids]

    def get_owned_count(self, player_name: str) -> int:
        return len(self.get_owned_prizes(player_name))

    def owns_prize(self, player_name: str, prize_id: str) -> bool:
        player = self.db.get_or_create_player(player_name)
        rows = self.db.execute(
            "SELECT 1 FROM player_prizes WHERE player_id = ? AND prize_id = ?",
            (player["id"], prize_id),
        )
        return len(rows) > 0

    def award_prize(self, player_name: str, prize_id: str, source: str = "achievement") -> bool:
        """
        Award a prize to a player. Returns True if newly awarded, False if already owned.
        """
        if prize_id not in PRIZE_MAP:
            return False
        player = self.db.get_or_create_player(player_name)
        try:
            self.db.execute_insert(
                """INSERT OR IGNORE INTO player_prizes
                   (player_id, prize_id, source) VALUES (?, ?, ?)""",
                (player["id"], prize_id, source),
            )
            return True
        except Exception:
            return False

    def remove_prize(self, player_name: str, prize_id: str) -> bool:
        """Remove a prize from a player (e.g. after losing a wager)."""
        player = self.db.get_or_create_player(player_name)
        affected = self.db.execute_update(
            "DELETE FROM player_prizes WHERE player_id = ? AND prize_id = ?",
            (player["id"], prize_id),
        )
        return affected > 0

    # ── Active Title / Badge ────────────────────────────────────

    def get_active_title(self, player_name: str) -> PrizeDef | None:
        """Get the player's highest-rarity title."""
        owned = self.get_owned_prizes(player_name)
        titles = [p for p in owned if p.prize_type == "title"]
        if not titles:
            return None
        titles.sort(key=lambda p: RARITY_ORDER.get(p.rarity, 0), reverse=True)
        return titles[0]

    def get_active_badge(self, player_name: str) -> PrizeDef | None:
        """Get the player's highest-rarity badge."""
        owned = self.get_owned_prizes(player_name)
        badges = [p for p in owned if p.prize_type == "badge"]
        if not badges:
            return None
        badges.sort(key=lambda p: RARITY_ORDER.get(p.rarity, 0), reverse=True)
        return badges[0]

    # ── Wagering ────────────────────────────────────────────────

    def get_wagerable_prizes(self, player_name: str, max_rarity: str = "epic") -> list[PrizeDef]:
        """
        Return prizes the player can wager.
        Legendary items marked as non-wagerable are excluded.
        Only prizes up to max_rarity can be wagered.
        """
        owned = self.get_owned_prizes(player_name)
        max_level = RARITY_ORDER.get(max_rarity, 3)
        return [
            p for p in owned
            if p.wagerable and RARITY_ORDER.get(p.rarity, 0) <= max_level
        ]

    def place_wager(
        self,
        player_name: str,
        prize_id: str,
        opponent_type: str = "ai_builtin",
        opponent_id: int | None = None,
    ) -> int | None:
        """
        Place a wager on a prize for an upcoming match.
        Returns wager ID or None if invalid.
        """
        if not self.owns_prize(player_name, prize_id):
            return None
        prize = PRIZE_MAP.get(prize_id)
        if not prize or not prize.wagerable:
            return None

        player = self.db.get_or_create_player(player_name)
        wager_id = self.db.execute_insert(
            """INSERT INTO active_wagers
               (player_id, prize_id, opponent_type, opponent_id)
               VALUES (?, ?, ?, ?)""",
            (player["id"], prize_id, opponent_type, opponent_id),
        )
        return wager_id

    def resolve_wager(self, wager_id: int, player_won: bool) -> dict[str, Any]:
        """
        Resolve a wager after a match.
        If player won: they keep their prize (wager cleared).
        If player lost: prize is removed from their ownership.
        Returns dict with result info.
        """
        rows = self.db.execute(
            "SELECT * FROM active_wagers WHERE id = ?", (wager_id,)
        )
        if not rows:
            return {"error": "Wager not found"}

        wager = dict(rows[0])
        player_rows = self.db.execute(
            "SELECT name FROM players WHERE id = ?", (wager["player_id"],)
        )
        player_name = dict(player_rows[0])["name"] if player_rows else "Unknown"

        if player_won:
            # Player keeps their prize — wager cleared
            self.db.execute_update(
                "UPDATE active_wagers SET status = 'won' WHERE id = ?",
                (wager_id,),
            )
            return {
                "result": "won",
                "prize_id": wager["prize_id"],
                "message": f"Victory! You keep your {PRIZE_MAP[wager['prize_id']].name}!",
            }
        else:
            # Player loses their prize
            self.remove_prize(player_name, wager["prize_id"])
            self.db.execute_update(
                "UPDATE active_wagers SET status = 'lost' WHERE id = ?",
                (wager_id,),
            )
            return {
                "result": "lost",
                "prize_id": wager["prize_id"],
                "message": f"Defeat! You lost your {PRIZE_MAP[wager['prize_id']].name}...",
            }

    def get_pending_wager(self, player_name: str) -> dict[str, Any] | None:
        """Get the current pending wager for a player."""
        player = self.db.get_or_create_player(player_name)
        rows = self.db.execute(
            """SELECT * FROM active_wagers
               WHERE player_id = ? AND status = 'pending'
               ORDER BY created_at DESC LIMIT 1""",
            (player["id"],),
        )
        return dict(rows[0]) if rows else None

    # ── Display Helpers ─────────────────────────────────────────

    def get_trophy_cabinet(self, player_name: str) -> dict[str, list[PrizeDef]]:
        """Return owned prizes grouped by type."""
        owned = self.get_owned_prizes(player_name)
        cabinet: dict[str, list[PrizeDef]] = {
            "title": [], "badge": [], "medal": [], "banner": [],
        }
        for p in owned:
            cabinet.setdefault(p.prize_type, []).append(p)
        # Sort each category by rarity (rarer first)
        for cat in cabinet.values():
            cat.sort(key=lambda p: RARITY_ORDER.get(p.rarity, 0), reverse=True)
        return cabinet

    def get_catalog_with_ownership(self, player_name: str) -> list[dict[str, Any]]:
        """Return the full catalog with ownership status."""
        owned_ids = {p.id for p in self.get_owned_prizes(player_name)}
        return [
            {"prize": p, "owned": p.id in owned_ids}
            for p in sorted(PRIZES, key=lambda x: (x.prize_type, RARITY_ORDER.get(x.rarity, 0)))
        ]
