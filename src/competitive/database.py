"""
SQLite database manager — persistent storage for rankings, stats, achievements.

Handles connection pooling, schema creation, and versioned migrations.
All data lives in data/chess_battle.db relative to the project root.
"""

from __future__ import annotations

import os
import sqlite3
import time
from contextlib import contextmanager
from typing import Any, Generator

from src.utils.constants import PROJECT_ROOT

# ─────────────────────────────────────────────────────────────────────────────
# Paths
# ─────────────────────────────────────────────────────────────────────────────
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
DB_PATH = os.path.join(DATA_DIR, "chess_battle.db")

# Current schema version — bump this when adding migrations
SCHEMA_VERSION = 1


def _ensure_data_dir() -> None:
    os.makedirs(DATA_DIR, exist_ok=True)


# ─────────────────────────────────────────────────────────────────────────────
# Schema DDL
# ─────────────────────────────────────────────────────────────────────────────
_SCHEMA_V1 = """
-- Schema version tracking
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Player profile (single-player for now, expandable to multi-player later)
CREATE TABLE IF NOT EXISTS players (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL UNIQUE,
    elo         INTEGER NOT NULL DEFAULT 1200,
    peak_elo    INTEGER NOT NULL DEFAULT 1200,
    tier        TEXT    NOT NULL DEFAULT 'Bronze',
    games_played INTEGER NOT NULL DEFAULT 0,
    wins        INTEGER NOT NULL DEFAULT 0,
    losses      INTEGER NOT NULL DEFAULT 0,
    draws       INTEGER NOT NULL DEFAULT 0,
    win_streak  INTEGER NOT NULL DEFAULT 0,
    best_streak INTEGER NOT NULL DEFAULT 0,
    total_time_played REAL NOT NULL DEFAULT 0.0,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- AI opponents have their own profiles in the same table structure
CREATE TABLE IF NOT EXISTS ai_opponents (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    difficulty  TEXT    NOT NULL UNIQUE,  -- RECRUIT, SOLDIER, CAPTAIN, GENERAL, MAGNUS
    name        TEXT    NOT NULL,
    elo         INTEGER NOT NULL,
    peak_elo    INTEGER NOT NULL,
    games_played INTEGER NOT NULL DEFAULT 0,
    wins        INTEGER NOT NULL DEFAULT 0,
    losses      INTEGER NOT NULL DEFAULT 0,
    draws       INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- Match history — every completed game
CREATE TABLE IF NOT EXISTS match_history (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id       INTEGER NOT NULL REFERENCES players(id),
    opponent_type   TEXT    NOT NULL,  -- 'ai_builtin', 'ai_external', 'player'
    opponent_id     INTEGER,          -- FK to ai_opponents or players
    opponent_name   TEXT    NOT NULL,
    player_color    TEXT    NOT NULL,  -- 'white' or 'black'
    result          TEXT    NOT NULL,  -- '1-0', '0-1', '1/2-1/2'
    player_won      INTEGER NOT NULL, -- 1=win, 0=loss, -1=draw
    player_elo_before   INTEGER NOT NULL,
    player_elo_after    INTEGER NOT NULL,
    opponent_elo_before INTEGER NOT NULL,
    opponent_elo_after  INTEGER NOT NULL,
    elo_change      INTEGER NOT NULL,
    moves_count     INTEGER NOT NULL DEFAULT 0,
    duration_seconds REAL   NOT NULL DEFAULT 0.0,
    opening_name    TEXT,
    accuracy        REAL,             -- player accuracy percentage
    game_mode       TEXT    NOT NULL DEFAULT 'casual',  -- 'casual', 'ranked', 'wager'
    pgn_path        TEXT,
    played_at       TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- Player statistics (aggregated per time period for quick lookup)
CREATE TABLE IF NOT EXISTS player_stats (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id   INTEGER NOT NULL REFERENCES players(id),
    stat_key    TEXT    NOT NULL,  -- e.g. 'total_captures', 'total_checks', 'avg_accuracy'
    stat_value  REAL    NOT NULL DEFAULT 0,
    updated_at  TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE(player_id, stat_key)
);

-- Index for fast leaderboard queries
CREATE INDEX IF NOT EXISTS idx_players_elo ON players(elo DESC);
CREATE INDEX IF NOT EXISTS idx_match_history_player ON match_history(player_id, played_at DESC);
CREATE INDEX IF NOT EXISTS idx_player_stats_key ON player_stats(player_id, stat_key);
"""

# Default AI opponents seeded on first run
_DEFAULT_AI_OPPONENTS = [
    ("RECRUIT",  "Recruit",             800,  800),
    ("SOLDIER",  "Soldier",            1200, 1200),
    ("CAPTAIN",  "Captain",            1600, 1600),
    ("GENERAL",  "General",            2000, 2000),
    ("MAGNUS",   "Supreme Commander",  2850, 2850),
]


class Database:
    """SQLite database manager — singleton-style, thread-safe via connection per call."""

    _instance: Database | None = None

    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or DB_PATH
        _ensure_data_dir()
        self._init_schema()

    @classmethod
    def get_instance(cls, db_path: str | None = None) -> Database:
        """Return (or create) singleton."""
        if cls._instance is None or (db_path and cls._instance.db_path != db_path):
            cls._instance = cls(db_path)
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton (for tests)."""
        cls._instance = None

    # ── Connection ──────────────────────────────────────────────

    @contextmanager
    def connect(self) -> Generator[sqlite3.Connection, None, None]:
        """Context manager yielding a connection with row_factory=Row."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def execute(self, sql: str, params: tuple = ()) -> list[sqlite3.Row]:
        """Execute a query and return all rows."""
        with self.connect() as conn:
            cursor = conn.execute(sql, params)
            return cursor.fetchall()

    def execute_insert(self, sql: str, params: tuple = ()) -> int:
        """Execute an INSERT and return the last row id."""
        with self.connect() as conn:
            cursor = conn.execute(sql, params)
            return cursor.lastrowid or 0

    def execute_update(self, sql: str, params: tuple = ()) -> int:
        """Execute UPDATE/DELETE and return rows affected."""
        with self.connect() as conn:
            cursor = conn.execute(sql, params)
            return cursor.rowcount

    # ── Schema ──────────────────────────────────────────────────

    def _init_schema(self) -> None:
        """Create tables if not present and run migrations."""
        with self.connect() as conn:
            # Check if schema_version table exists
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'"
            )
            if not cursor.fetchone():
                # Fresh database — run full schema
                conn.executescript(_SCHEMA_V1)
                conn.execute(
                    "INSERT INTO schema_version (version) VALUES (?)",
                    (SCHEMA_VERSION,),
                )
                self._seed_ai_opponents(conn)
            else:
                # Check version and run migrations if needed
                row = conn.execute(
                    "SELECT MAX(version) as v FROM schema_version"
                ).fetchone()
                current = row["v"] if row else 0
                if current < SCHEMA_VERSION:
                    self._run_migrations(conn, current)

    def _seed_ai_opponents(self, conn: sqlite3.Connection) -> None:
        """Insert default AI opponents."""
        for difficulty, name, elo, peak_elo in _DEFAULT_AI_OPPONENTS:
            conn.execute(
                """INSERT OR IGNORE INTO ai_opponents
                   (difficulty, name, elo, peak_elo) VALUES (?, ?, ?, ?)""",
                (difficulty, name, elo, peak_elo),
            )

    def _run_migrations(self, conn: sqlite3.Connection, from_version: int) -> None:
        """Run incremental migrations. Add new migration blocks here."""
        # Example:
        # if from_version < 2:
        #     conn.executescript(_MIGRATION_V2)
        #     conn.execute("INSERT INTO schema_version (version) VALUES (2)")
        pass

    # ── Convenience ─────────────────────────────────────────────

    def get_or_create_player(self, name: str = "Player") -> dict[str, Any]:
        """Get existing player or create a new one. Returns dict."""
        rows = self.execute(
            "SELECT * FROM players WHERE name = ?", (name,)
        )
        if rows:
            return dict(rows[0])

        player_id = self.execute_insert(
            "INSERT INTO players (name) VALUES (?)", (name,)
        )
        rows = self.execute("SELECT * FROM players WHERE id = ?", (player_id,))
        return dict(rows[0])

    def get_ai_opponent(self, difficulty: str) -> dict[str, Any] | None:
        """Get an AI opponent by difficulty key."""
        rows = self.execute(
            "SELECT * FROM ai_opponents WHERE difficulty = ?", (difficulty,)
        )
        return dict(rows[0]) if rows else None

    def get_all_ai_opponents(self) -> list[dict[str, Any]]:
        """Get all AI opponents."""
        rows = self.execute("SELECT * FROM ai_opponents ORDER BY elo ASC")
        return [dict(r) for r in rows]
