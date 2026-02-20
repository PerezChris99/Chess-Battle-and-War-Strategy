"""
Phase 8 Tests — Achievements & Prizes.

Tests the achievement detection engine, prize management,
wagering mechanics, and integration between the two systems.
"""

import os
import tempfile
import pytest

from src.competitive.database import Database
from src.competitive.achievements import (
    AchievementEngine, ACHIEVEMENTS, ACHIEVEMENT_MAP, CATEGORIES,
    AchievementDef,
)
from src.competitive.prizes import (
    PrizeManager, PRIZES, PRIZE_MAP, PRIZE_TYPES, RARITY_ORDER,
    PrizeDef,
)
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
def achievements(temp_db):
    return AchievementEngine(temp_db)


@pytest.fixture
def prizes(temp_db):
    return PrizeManager(temp_db)


@pytest.fixture
def stats(temp_db):
    return StatsTracker(temp_db)


# ─────────────────────────────────────────────────────────────────────────────
# Achievement Catalog Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestAchievementCatalog:
    def test_catalog_has_achievements(self):
        assert len(ACHIEVEMENTS) >= 30

    def test_unique_ids(self):
        ids = [a.id for a in ACHIEVEMENTS]
        assert len(ids) == len(set(ids)), "Duplicate achievement IDs"

    def test_all_have_required_fields(self):
        for a in ACHIEVEMENTS:
            assert a.id
            assert a.name
            assert a.description
            assert a.category
            assert a.rarity in ("common", "uncommon", "rare", "epic", "legendary")

    def test_categories_populated(self):
        assert len(CATEGORIES) >= 8

    def test_map_matches_list(self):
        assert len(ACHIEVEMENT_MAP) == len(ACHIEVEMENTS)
        for a in ACHIEVEMENTS:
            assert ACHIEVEMENT_MAP[a.id] is a


# ─────────────────────────────────────────────────────────────────────────────
# Achievement Engine — Stat-Based Unlocks
# ─────────────────────────────────────────────────────────────────────────────

class TestStatBasedAchievements:
    def test_no_unlocks_initially(self, achievements):
        earned = achievements.get_earned("Tester")
        assert earned == []

    def test_first_win_unlock(self, achievements, stats, temp_db):
        """Winning 1 game should unlock 'first_win'."""
        stats.increment_stat("Tester", "total_wins")
        unlocked = achievements.check_unlocks("Tester")
        ids = [a.id for a in unlocked]
        assert "first_win" in ids

    def test_no_double_unlock(self, achievements, stats, temp_db):
        """Already-earned achievements shouldn't fire again."""
        stats.increment_stat("Tester", "total_wins")
        achievements.check_unlocks("Tester")
        # Check again — should not re-unlock
        unlocked2 = achievements.check_unlocks("Tester")
        ids2 = [a.id for a in unlocked2]
        assert "first_win" not in ids2

    def test_play_10_games(self, achievements, stats):
        for _ in range(10):
            stats.increment_stat("Tester", "total_games")
        unlocked = achievements.check_unlocks("Tester")
        ids = [a.id for a in unlocked]
        assert "play_10" in ids

    def test_captures_50(self, achievements, stats):
        stats.set_stat("Tester", "total_captures", 50)
        unlocked = achievements.check_unlocks("Tester")
        ids = [a.id for a in unlocked]
        assert "captures_50" in ids

    def test_checks_25(self, achievements, stats):
        stats.set_stat("Tester", "total_checks", 25)
        unlocked = achievements.check_unlocks("Tester")
        ids = [a.id for a in unlocked]
        assert "checks_25" in ids

    def test_accuracy_80(self, achievements, stats):
        stats.set_stat("Tester", "best_accuracy", 82)
        unlocked = achievements.check_unlocks("Tester")
        ids = [a.id for a in unlocked]
        assert "accuracy_80" in ids

    def test_fast_win(self, achievements, stats):
        stats.set_stat("Tester", "fast_wins", 1)
        unlocked = achievements.check_unlocks("Tester")
        ids = [a.id for a in unlocked]
        assert "fast_win" in ids


# ─────────────────────────────────────────────────────────────────────────────
# Achievement Engine — Custom Logic Unlocks
# ─────────────────────────────────────────────────────────────────────────────

class TestCustomAchievements:
    def test_tier_silver(self, achievements, temp_db):
        """Player at 1100+ ELO should unlock reach_silver."""
        player = temp_db.get_or_create_player("Tester")
        temp_db.execute_update(
            "UPDATE players SET elo = ? WHERE id = ?", (1100, player["id"])
        )
        unlocked = achievements.check_unlocks("Tester")
        ids = [a.id for a in unlocked]
        assert "reach_silver" in ids

    def test_tier_gold(self, achievements, temp_db):
        player = temp_db.get_or_create_player("Tester")
        temp_db.execute_update(
            "UPDATE players SET elo = ? WHERE id = ?", (1400, player["id"])
        )
        unlocked = achievements.check_unlocks("Tester")
        ids = [a.id for a in unlocked]
        assert "reach_gold" in ids

    def test_giant_slayer_soldier(self, achievements):
        unlocked = achievements.check_unlocks(
            "Tester",
            match_result={"difficulty": "SOLDIER", "player_won": True},
        )
        ids = [a.id for a in unlocked]
        assert "beat_soldier" in ids

    def test_giant_slayer_not_on_loss(self, achievements):
        unlocked = achievements.check_unlocks(
            "Tester",
            match_result={"difficulty": "SOLDIER", "player_won": False},
        )
        ids = [a.id for a in unlocked]
        assert "beat_soldier" not in ids

    def test_giant_slayer_magnus(self, achievements):
        unlocked = achievements.check_unlocks(
            "Tester",
            match_result={"difficulty": "MAGNUS", "player_won": True},
        )
        ids = [a.id for a in unlocked]
        assert "beat_magnus" in ids

    def test_streak_3(self, achievements, temp_db):
        player = temp_db.get_or_create_player("Tester")
        temp_db.execute_update(
            "UPDATE players SET best_streak = ? WHERE id = ?", (3, player["id"])
        )
        unlocked = achievements.check_unlocks("Tester")
        ids = [a.id for a in unlocked]
        assert "streak_3" in ids

    def test_streak_5(self, achievements, temp_db):
        player = temp_db.get_or_create_player("Tester")
        temp_db.execute_update(
            "UPDATE players SET best_streak = ? WHERE id = ?", (5, player["id"])
        )
        unlocked = achievements.check_unlocks("Tester")
        ids = [a.id for a in unlocked]
        assert "streak_5" in ids


# ─────────────────────────────────────────────────────────────────────────────
# Achievement Progress Tracking
# ─────────────────────────────────────────────────────────────────────────────

class TestAchievementProgress:
    def test_progress_starts_at_zero(self, achievements):
        progress = achievements.get_progress("Tester")
        for p in progress:
            if p["achievement"].stat_key and p["achievement"].threshold > 0:
                assert p["progress_pct"] == 0.0
            assert not p["earned"]

    def test_partial_progress(self, achievements, stats):
        stats.set_stat("Tester", "total_games", 5)
        progress = achievements.get_progress("Tester")
        play_10 = next(p for p in progress if p["achievement"].id == "play_10")
        assert 49 <= play_10["progress_pct"] <= 51  # ~50%
        assert not play_10["earned"]

    def test_earned_shows_100_percent(self, achievements, stats):
        stats.set_stat("Tester", "total_wins", 1)
        achievements.check_unlocks("Tester")
        progress = achievements.get_progress("Tester")
        first_win = next(p for p in progress if p["achievement"].id == "first_win")
        assert first_win["earned"]
        assert first_win["progress_pct"] == 100.0

    def test_earned_count(self, achievements, stats):
        assert achievements.get_earned_count("Tester") == 0
        stats.set_stat("Tester", "total_wins", 1)
        achievements.check_unlocks("Tester")
        assert achievements.get_earned_count("Tester") >= 1


# ─────────────────────────────────────────────────────────────────────────────
# Prize Catalog Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestPrizeCatalog:
    def test_catalog_has_prizes(self):
        assert len(PRIZES) >= 20

    def test_unique_ids(self):
        ids = [p.id for p in PRIZES]
        assert len(ids) == len(set(ids)), "Duplicate prize IDs"

    def test_all_have_required_fields(self):
        for p in PRIZES:
            assert p.id
            assert p.name
            assert p.prize_type in ("title", "badge", "medal", "banner")
            assert p.rarity in RARITY_ORDER

    def test_prize_types(self):
        assert set(PRIZE_TYPES) >= {"title", "badge", "medal", "banner"}

    def test_map_matches_list(self):
        assert len(PRIZE_MAP) == len(PRIZES)

    def test_rarity_order(self):
        assert RARITY_ORDER["common"] < RARITY_ORDER["legendary"]


# ─────────────────────────────────────────────────────────────────────────────
# Prize Ownership
# ─────────────────────────────────────────────────────────────────────────────

class TestPrizeOwnership:
    def test_no_prizes_initially(self, prizes):
        owned = prizes.get_owned_prizes("Tester")
        assert owned == []

    def test_award_prize(self, prizes):
        result = prizes.award_prize("Tester", "title_warrior")
        assert result is True
        assert prizes.owns_prize("Tester", "title_warrior")

    def test_duplicate_award_idempotent(self, prizes):
        prizes.award_prize("Tester", "title_warrior")
        prizes.award_prize("Tester", "title_warrior")
        assert prizes.get_owned_count("Tester") == 1

    def test_award_invalid_prize(self, prizes):
        result = prizes.award_prize("Tester", "nonexistent_prize_xyz")
        assert result is False

    def test_remove_prize(self, prizes):
        prizes.award_prize("Tester", "title_warrior")
        removed = prizes.remove_prize("Tester", "title_warrior")
        assert removed is True
        assert not prizes.owns_prize("Tester", "title_warrior")

    def test_remove_unowned_prize(self, prizes):
        removed = prizes.remove_prize("Tester", "title_warrior")
        assert removed is False

    def test_owned_count(self, prizes):
        prizes.award_prize("Tester", "title_warrior")
        prizes.award_prize("Tester", "badge_shield")
        prizes.award_prize("Tester", "medal_bronze_star")
        assert prizes.get_owned_count("Tester") == 3

    def test_multiple_sources(self, prizes):
        prizes.award_prize("Tester", "title_warrior", "achievement")
        prizes.award_prize("Tester", "badge_shield", "wager")
        assert prizes.get_owned_count("Tester") == 2


# ─────────────────────────────────────────────────────────────────────────────
# Active Title & Badge
# ─────────────────────────────────────────────────────────────────────────────

class TestActivePrize:
    def test_no_active_title_initially(self, prizes):
        assert prizes.get_active_title("Tester") is None

    def test_active_title_highest_rarity(self, prizes):
        prizes.award_prize("Tester", "title_warrior")        # common
        prizes.award_prize("Tester", "title_war_machine")    # epic
        active = prizes.get_active_title("Tester")
        assert active is not None
        assert active.id == "title_war_machine"

    def test_active_badge(self, prizes):
        prizes.award_prize("Tester", "badge_shield")         # common
        prizes.award_prize("Tester", "badge_gold_crown")     # rare
        active = prizes.get_active_badge("Tester")
        assert active is not None
        assert active.id == "badge_gold_crown"


# ─────────────────────────────────────────────────────────────────────────────
# Wagering
# ─────────────────────────────────────────────────────────────────────────────

class TestWagering:
    def test_place_wager(self, prizes):
        prizes.award_prize("Tester", "title_warrior")
        wager_id = prizes.place_wager("Tester", "title_warrior")
        assert wager_id is not None
        assert isinstance(wager_id, int)

    def test_wager_unowned_fails(self, prizes):
        wager_id = prizes.place_wager("Tester", "title_warrior")
        assert wager_id is None

    def test_wager_non_wagerable_fails(self, prizes):
        # title_magnus_rival is not wagerable
        prizes.award_prize("Tester", "title_magnus_rival")
        wager_id = prizes.place_wager("Tester", "title_magnus_rival")
        assert wager_id is None

    def test_wager_win_keeps_prize(self, prizes):
        prizes.award_prize("Tester", "badge_shield")
        wager_id = prizes.place_wager("Tester", "badge_shield")
        result = prizes.resolve_wager(wager_id, player_won=True)
        assert result["result"] == "won"
        assert prizes.owns_prize("Tester", "badge_shield")

    def test_wager_loss_removes_prize(self, prizes):
        prizes.award_prize("Tester", "badge_shield")
        wager_id = prizes.place_wager("Tester", "badge_shield")
        result = prizes.resolve_wager(wager_id, player_won=False)
        assert result["result"] == "lost"
        assert not prizes.owns_prize("Tester", "badge_shield")

    def test_resolve_invalid_wager(self, prizes):
        result = prizes.resolve_wager(9999, player_won=True)
        assert "error" in result

    def test_pending_wager(self, prizes):
        prizes.award_prize("Tester", "title_warrior")
        prizes.place_wager("Tester", "title_warrior")
        pending = prizes.get_pending_wager("Tester")
        assert pending is not None
        assert pending["prize_id"] == "title_warrior"

    def test_no_pending_after_resolve(self, prizes):
        prizes.award_prize("Tester", "title_warrior")
        wager_id = prizes.place_wager("Tester", "title_warrior")
        prizes.resolve_wager(wager_id, player_won=True)
        pending = prizes.get_pending_wager("Tester")
        assert pending is None

    def test_wagerable_filter(self, prizes):
        prizes.award_prize("Tester", "title_warrior")        # common, wagerable
        prizes.award_prize("Tester", "title_magnus_rival")   # legendary, not wagerable
        wagerable = prizes.get_wagerable_prizes("Tester")
        ids = [p.id for p in wagerable]
        assert "title_warrior" in ids
        assert "title_magnus_rival" not in ids


# ─────────────────────────────────────────────────────────────────────────────
# Trophy Cabinet
# ─────────────────────────────────────────────────────────────────────────────

class TestTrophyCabinet:
    def test_empty_cabinet(self, prizes):
        cabinet = prizes.get_trophy_cabinet("Tester")
        assert all(len(v) == 0 for v in cabinet.values())

    def test_cabinet_grouped_by_type(self, prizes):
        prizes.award_prize("Tester", "title_warrior")
        prizes.award_prize("Tester", "badge_shield")
        prizes.award_prize("Tester", "medal_bronze_star")
        prizes.award_prize("Tester", "banner_battlefield_dawn")
        cabinet = prizes.get_trophy_cabinet("Tester")
        assert len(cabinet["title"]) == 1
        assert len(cabinet["badge"]) == 1
        assert len(cabinet["medal"]) == 1
        assert len(cabinet["banner"]) == 1

    def test_cabinet_sorted_by_rarity(self, prizes):
        prizes.award_prize("Tester", "title_warrior")        # common
        prizes.award_prize("Tester", "title_war_machine")    # epic
        cabinet = prizes.get_trophy_cabinet("Tester")
        titles = cabinet["title"]
        assert titles[0].id == "title_war_machine"  # epic first
        assert titles[1].id == "title_warrior"       # common second

    def test_catalog_with_ownership(self, prizes):
        prizes.award_prize("Tester", "title_warrior")
        catalog = prizes.get_catalog_with_ownership("Tester")
        assert len(catalog) == len(PRIZES)
        warrior = next(c for c in catalog if c["prize"].id == "title_warrior")
        assert warrior["owned"] is True
        shield = next(c for c in catalog if c["prize"].id == "badge_shield")
        assert shield["owned"] is False


# ─────────────────────────────────────────────────────────────────────────────
# Achievement ↔ Prize Integration
# ─────────────────────────────────────────────────────────────────────────────

class TestAchievementPrizeIntegration:
    def test_first_win_awards_prize(self, achievements, prizes, stats):
        """Unlocking 'first_win' should award 'title_warrior' prize."""
        stats.increment_stat("Tester", "total_wins")
        unlocked = achievements.check_unlocks("Tester")
        # Award linked prizes
        for ach in unlocked:
            if ach.prize_id:
                prizes.award_prize("Tester", ach.prize_id)
        assert prizes.owns_prize("Tester", "title_warrior")

    def test_giant_slayer_captain_awards_badge(self, achievements, prizes):
        unlocked = achievements.check_unlocks(
            "Tester",
            match_result={"difficulty": "CAPTAIN", "player_won": True},
        )
        for ach in unlocked:
            if ach.prize_id:
                prizes.award_prize("Tester", ach.prize_id)
        assert prizes.owns_prize("Tester", "badge_crossed_swords")

    def test_recent_unlocks_cleared(self, achievements, stats):
        """recent_unlocks property should clear after reading."""
        stats.increment_stat("Tester", "total_wins")
        achievements.check_unlocks("Tester")
        first = achievements.recent_unlocks
        assert len(first) >= 1
        second = achievements.recent_unlocks
        assert len(second) == 0
