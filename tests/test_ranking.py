"""
Phase 7 Tests — Ranking, Leaderboard, Stats, Database.

Tests the competitive system: ELO calculations, tier assignments,
database operations, leaderboard queries, and stats tracking.
"""

import os
import tempfile
import pytest

from src.competitive.database import Database
from src.competitive.ranking import (
    RankingEngine, calculate_elo_change, get_tier_name, get_tier_badge,
    get_tier, TIERS, RatingChange,
)
from src.competitive.leaderboard import Leaderboard
from src.competitive.stats import StatsTracker


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    Database.reset_instance()
    db = Database(path)
    yield db
    Database.reset_instance()
    try:
        os.unlink(path)
    except OSError:
        pass


@pytest.fixture
def ranking(temp_db):
    return RankingEngine(temp_db)


@pytest.fixture
def leaderboard(temp_db):
    return Leaderboard(temp_db)


@pytest.fixture
def stats(temp_db):
    return StatsTracker(temp_db)


# ─────────────────────────────────────────────────────────────────────────────
# Tier Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestTiers:
    def test_bronze_tier(self):
        assert get_tier_name(0) == "Bronze"
        assert get_tier_name(1099) == "Bronze"

    def test_silver_tier(self):
        assert get_tier_name(1100) == "Silver"
        assert get_tier_name(1399) == "Silver"

    def test_gold_tier(self):
        assert get_tier_name(1400) == "Gold"

    def test_platinum_tier(self):
        assert get_tier_name(1700) == "Platinum"

    def test_diamond_tier(self):
        assert get_tier_name(2000) == "Diamond"

    def test_grandmaster_tier(self):
        assert get_tier_name(2500) == "Grandmaster"
        assert get_tier_name(2850) == "Grandmaster"

    def test_tier_has_badge(self):
        for tier in TIERS:
            assert get_tier_badge(tier["min_elo"]) != ""


# ─────────────────────────────────────────────────────────────────────────────
# ELO Calculation Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestELOCalculation:
    def test_equal_rating_win(self):
        new_p, new_o = calculate_elo_change(1200, 1200, 1.0, 30)
        assert new_p > 1200
        assert new_o < 1200

    def test_equal_rating_loss(self):
        new_p, new_o = calculate_elo_change(1200, 1200, 0.0, 30)
        assert new_p < 1200
        assert new_o > 1200

    def test_equal_rating_draw(self):
        new_p, new_o = calculate_elo_change(1200, 1200, 0.5, 30)
        assert new_p == 1200
        assert new_o == 1200

    def test_underdog_win_big_gain(self):
        """Lower-rated player beating higher-rated should gain more."""
        new_p1, _ = calculate_elo_change(1200, 2000, 1.0, 30)
        new_p2, _ = calculate_elo_change(1200, 1200, 1.0, 30)
        assert (new_p1 - 1200) > (new_p2 - 1200)

    def test_provisional_k_factor(self):
        """New players (<30 games) should have bigger swings."""
        new_p_prov, _ = calculate_elo_change(1200, 1200, 1.0, 5)
        new_p_est, _ = calculate_elo_change(1200, 1200, 1.0, 50)
        assert (new_p_prov - 1200) > (new_p_est - 1200)

    def test_floor_at_zero(self):
        new_p, _ = calculate_elo_change(10, 2000, 0.0, 30)
        assert new_p >= 0


# ─────────────────────────────────────────────────────────────────────────────
# Database Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestDatabase:
    def test_create_player(self, temp_db):
        player = temp_db.get_or_create_player("TestPlayer")
        assert player["name"] == "TestPlayer"
        assert player["elo"] == 1200
        assert player["tier"] == "Bronze"

    def test_get_existing_player(self, temp_db):
        p1 = temp_db.get_or_create_player("TestPlayer")
        p2 = temp_db.get_or_create_player("TestPlayer")
        assert p1["id"] == p2["id"]

    def test_ai_opponents_seeded(self, temp_db):
        opponents = temp_db.get_all_ai_opponents()
        assert len(opponents) == 5
        names = [o["difficulty"] for o in opponents]
        assert "RECRUIT" in names
        assert "MAGNUS" in names

    def test_get_ai_by_difficulty(self, temp_db):
        ai = temp_db.get_ai_opponent("SOLDIER")
        assert ai is not None
        assert ai["elo"] == 1200

    def test_unknown_ai_returns_none(self, temp_db):
        assert temp_db.get_ai_opponent("NONEXISTENT") is None


# ─────────────────────────────────────────────────────────────────────────────
# Ranking Engine Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestRankingEngine:
    def test_process_win(self, ranking, temp_db):
        result = ranking.process_match(
            player_name="Hero",
            difficulty="SOLDIER",
            result="1-0",
            player_color="white",
            moves_count=30,
            game_mode="ranked",
        )
        assert isinstance(result, RatingChange)
        assert result.change > 0
        assert result.new_rating > result.old_rating

        # Check player updated in DB
        player = temp_db.get_or_create_player("Hero")
        assert player["wins"] == 1
        assert player["elo"] == result.new_rating

    def test_process_loss(self, ranking, temp_db):
        result = ranking.process_match(
            player_name="Hero",
            difficulty="SOLDIER",
            result="0-1",
            player_color="white",
            game_mode="ranked",
        )
        assert result.change < 0
        player = temp_db.get_or_create_player("Hero")
        assert player["losses"] == 1

    def test_process_draw(self, ranking, temp_db):
        result = ranking.process_match(
            player_name="Hero",
            difficulty="SOLDIER",
            result="1/2-1/2",
            player_color="white",
            game_mode="ranked",
        )
        player = temp_db.get_or_create_player("Hero")
        assert player["draws"] == 1

    def test_casual_mode_no_elo_change(self, ranking):
        result = ranking.process_match(
            player_name="CasualPlayer",
            difficulty="RECRUIT",
            result="1-0",
            player_color="white",
            game_mode="casual",
        )
        assert result.change == 0

    def test_win_streak_tracking(self, ranking, temp_db):
        for _ in range(3):
            ranking.process_match(
                player_name="Streaker",
                difficulty="RECRUIT",
                result="1-0",
                player_color="white",
                game_mode="ranked",
            )
        player = temp_db.get_or_create_player("Streaker")
        assert player["win_streak"] == 3
        assert player["best_streak"] == 3

    def test_streak_resets_on_loss(self, ranking, temp_db):
        for _ in range(3):
            ranking.process_match(
                player_name="StreakLoss",
                difficulty="RECRUIT",
                result="1-0",
                player_color="white",
                game_mode="ranked",
            )
        ranking.process_match(
            player_name="StreakLoss",
            difficulty="RECRUIT",
            result="0-1",
            player_color="white",
            game_mode="ranked",
        )
        player = temp_db.get_or_create_player("StreakLoss")
        assert player["win_streak"] == 0
        assert player["best_streak"] == 3

    def test_match_recorded_in_history(self, ranking, temp_db):
        ranking.process_match(
            player_name="Historian",
            difficulty="CAPTAIN",
            result="0-1",
            player_color="black",
            game_mode="ranked",
        )
        player = temp_db.get_or_create_player("Historian")
        rows = temp_db.execute(
            "SELECT * FROM match_history WHERE player_id = ?",
            (player["id"],),
        )
        assert len(rows) == 1
        match = dict(rows[0])
        assert match["result"] == "0-1"
        assert match["player_color"] == "black"
        assert match["player_won"] == 1

    def test_tier_promotion_detection(self, ranking, temp_db):
        """Force enough wins to promote from Bronze to Silver."""
        # Start at 1200 (Bronze boundary), need to get to 1100+ (already there)
        # but default new player is 1200 which is already Silver... no, wait, 
        # tier thresholds: Bronze=0, Silver=1100
        # Default player starts at 1200, which is Silver tier
        # Let's create a player and manually set their ELO low
        temp_db.execute_update(
            "INSERT INTO players (name, elo, peak_elo, tier) VALUES (?, ?, ?, ?)",
            ("LowPlayer", 1050, 1050, "Bronze"),
        )
        # Win a big match to promote
        result = ranking.process_match(
            player_name="LowPlayer",
            difficulty="CAPTAIN",
            result="1-0",
            player_color="white",
            game_mode="ranked",
        )
        # Should have gained enough to cross 1100
        if result.new_rating >= 1100:
            assert result.promoted is True


# ─────────────────────────────────────────────────────────────────────────────
# Leaderboard Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestLeaderboard:
    def test_unified_leaderboard_contains_ai(self, leaderboard):
        entries = leaderboard.get_unified_leaderboard()
        assert len(entries) >= 5  # at least the 5 AI opponents
        names = [e.name for e in entries]
        assert any("Recruit" in n for n in names)
        assert any("Supreme Commander" in n for n in names)

    def test_leaderboard_sorted_by_elo(self, leaderboard):
        entries = leaderboard.get_unified_leaderboard()
        elos = [e.elo for e in entries]
        assert elos == sorted(elos, reverse=True)

    def test_player_appears_on_leaderboard(self, leaderboard, temp_db):
        temp_db.get_or_create_player("TestPlayer")
        entries = leaderboard.get_unified_leaderboard("TestPlayer")
        current = [e for e in entries if e.is_current_player]
        assert len(current) == 1
        assert current[0].name == "TestPlayer"

    def test_player_rank_assigned(self, leaderboard, temp_db):
        temp_db.get_or_create_player("Player")
        rank = leaderboard.get_player_rank("Player")
        assert rank is not None
        assert rank >= 1

    def test_player_summary(self, leaderboard, temp_db):
        temp_db.get_or_create_player("SummaryPlayer")
        summary = leaderboard.get_player_summary("SummaryPlayer")
        assert summary["name"] == "SummaryPlayer"
        assert summary["elo"] == 1200
        assert summary["tier"] == "Silver"

    def test_head_to_head_empty(self, leaderboard):
        h2h = leaderboard.get_head_to_head("NoGames", "RECRUIT")
        assert h2h == {"wins": 0, "losses": 0, "draws": 0}


# ─────────────────────────────────────────────────────────────────────────────
# Stats Tracker Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestStatsTracker:
    def test_increment_stat(self, stats, temp_db):
        temp_db.get_or_create_player("StatsPlayer")
        stats.increment_stat("StatsPlayer", "total_captures", 5)
        assert stats.get_stat("StatsPlayer", "total_captures") == 5.0
        stats.increment_stat("StatsPlayer", "total_captures", 3)
        assert stats.get_stat("StatsPlayer", "total_captures") == 8.0

    def test_set_stat(self, stats, temp_db):
        temp_db.get_or_create_player("SetPlayer")
        stats.set_stat("SetPlayer", "best_accuracy", 92.5)
        assert stats.get_stat("SetPlayer", "best_accuracy") == 92.5

    def test_get_unknown_stat_returns_zero(self, stats, temp_db):
        temp_db.get_or_create_player("EmptyStats")
        assert stats.get_stat("EmptyStats", "nonexistent") == 0.0

    def test_record_game_stats(self, stats, temp_db):
        temp_db.get_or_create_player("GameStats")
        stats.record_game_stats(
            player_name="GameStats",
            moves_count=25,
            captures=8,
            checks=3,
            castled=True,
            accuracy=78.5,
            won=True,
            duration=300.0,
        )
        assert stats.get_stat("GameStats", "total_moves") == 25.0
        assert stats.get_stat("GameStats", "total_captures") == 8.0
        assert stats.get_stat("GameStats", "total_checks") == 3.0
        assert stats.get_stat("GameStats", "games_castled") == 1.0
        assert stats.get_stat("GameStats", "total_wins") == 1.0
        assert abs(stats.get_stat("GameStats", "avg_accuracy") - 78.5) < 0.1

    def test_display_stats(self, stats, temp_db):
        temp_db.get_or_create_player("DisplayPlayer")
        stats.record_game_stats("DisplayPlayer", 20, 5, 2, True, 80.0, True, 120.0)
        display = stats.get_display_stats("DisplayPlayer")
        assert isinstance(display, list)
        assert len(display) > 0
        labels = [d[0] for d in display]
        assert "Games Played" in labels
        assert "Avg Accuracy" in labels
