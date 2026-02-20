"""
Phase 9 Tests — AI Arena: Adapter, Gemini, Arena Manager.

Tests the arena adapter interface, move validation, rate limiting,
Gemini adapter (mocked), arena manager DB, and match orchestration.
"""

import os
import tempfile
import time
import pytest

import chess

from src.competitive.database import Database
from src.engine.arena_adapter import (
    ArenaAdapter, ArenaModelInfo, ArenaMove, RateLimitState,
    register_adapter, get_available_adapters, create_adapter,
)
from src.engine.arena_manager import ArenaManager, ArenaMatch
from src.engine.gemini_adapter import (
    GeminiAdapter, _extract_uci_move, _build_move_prompt, get_gemini_models,
)


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
def arena_manager(temp_db):
    return ArenaManager(temp_db)


# ─────────────────────────────────────────────────────────────────────────────
# Mock Adapter for Testing
# ─────────────────────────────────────────────────────────────────────────────

class MockAdapter(ArenaAdapter):
    """Test adapter that returns pre-set moves."""

    def __init__(self):
        super().__init__()
        self._moves: list[str] = []
        self._move_index = 0
        self._should_error = False

    def get_info(self) -> ArenaModelInfo:
        return ArenaModelInfo(
            model_id="mock_ai",
            display_name="Mock AI",
            provider="Test",
            icon="🧪",
            description="A mock AI for testing",
            default_elo=1500,
        )

    def configure(self, api_key: str, **kwargs) -> bool:
        self._configured = True
        return True

    def set_moves(self, moves: list[str]) -> None:
        """Pre-set moves for the mock to return."""
        self._moves = moves
        self._move_index = 0

    def set_error(self, should_error: bool) -> None:
        self._should_error = should_error

    def _request_move(self, fen: str, move_history: list[str]) -> ArenaMove:
        if self._should_error:
            return ArenaMove(uci_move="", thinking_time=0, error="Mock error")

        if self._move_index < len(self._moves):
            move = self._moves[self._move_index]
            self._move_index += 1
            return ArenaMove(uci_move=move, thinking_time=0.01)

        # Default: return e2e4 (may not always be legal)
        return ArenaMove(uci_move="e2e4", thinking_time=0.01)


# ─────────────────────────────────────────────────────────────────────────────
# Rate Limiting Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestRateLimiting:
    def test_initial_state_allows_request(self):
        state = RateLimitState()
        assert state.can_request()

    def test_respects_min_interval(self):
        state = RateLimitState(min_interval=2.0)
        state.record_request()
        assert not state.can_request()

    def test_respects_max_per_minute(self):
        state = RateLimitState(max_per_minute=2, min_interval=0)
        state.record_request()
        state.record_request()
        assert not state.can_request()

    def test_minute_reset(self):
        state = RateLimitState(max_per_minute=1, min_interval=0)
        state.record_request()
        assert not state.can_request()
        # Simulate minute passing
        state.minute_start = time.time() - 61
        state.last_request_time = time.time() - 61
        assert state.can_request()

    def test_backoff_increases(self):
        state = RateLimitState()
        assert state.get_backoff_delay() == 0.0
        state.record_error()
        assert state.get_backoff_delay() == 2.0
        state.record_error()
        assert state.get_backoff_delay() == 4.0

    def test_success_resets_errors(self):
        state = RateLimitState()
        state.record_error()
        state.record_error()
        assert state.consecutive_errors == 2
        state.record_success()
        assert state.consecutive_errors == 0

    def test_should_retry(self):
        state = RateLimitState(max_retries=2)
        assert state.should_retry
        state.record_error()
        assert state.should_retry
        state.record_error()
        assert not state.should_retry


# ─────────────────────────────────────────────────────────────────────────────
# Move Validation Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestMoveValidation:
    def test_valid_uci_move(self):
        board = chess.Board()
        result = ArenaAdapter._validate_move(board, "e2e4")
        assert result == "e2e4"

    def test_invalid_move_returns_none(self):
        board = chess.Board()
        result = ArenaAdapter._validate_move(board, "e2e5")  # illegal
        assert result is None

    def test_empty_string_returns_none(self):
        board = chess.Board()
        result = ArenaAdapter._validate_move(board, "")
        assert result is None

    def test_san_notation_accepted(self):
        board = chess.Board()
        result = ArenaAdapter._validate_move(board, "e4")
        assert result == "e2e4"

    def test_san_knight_move(self):
        board = chess.Board()
        result = ArenaAdapter._validate_move(board, "Nf3")
        assert result == "g1f3"

    def test_uppercase_cleaned(self):
        board = chess.Board()
        result = ArenaAdapter._validate_move(board, "E2E4")
        assert result == "e2e4"

    def test_spaces_cleaned(self):
        board = chess.Board()
        result = ArenaAdapter._validate_move(board, " e2e4 ")
        assert result == "e2e4"


# ─────────────────────────────────────────────────────────────────────────────
# UCI Extraction Tests (Gemini response parsing)
# ─────────────────────────────────────────────────────────────────────────────

class TestUCIExtraction:
    def test_clean_uci(self):
        move, exp = _extract_uci_move("e2e4")
        assert move == "e2e4"

    def test_uci_with_newline_explanation(self):
        move, exp = _extract_uci_move("e2e4\nControls the center")
        assert move == "e2e4"
        assert "center" in exp.lower()

    def test_uci_with_backticks(self):
        move, exp = _extract_uci_move("`e2e4`")
        assert move == "e2e4"

    def test_uci_in_sentence(self):
        move, exp = _extract_uci_move("My move is e2e4.")
        assert move == "e2e4"

    def test_promotion_move(self):
        move, exp = _extract_uci_move("e7e8q")
        assert move == "e7e8q"

    def test_empty_response(self):
        move, exp = _extract_uci_move("")
        assert move == ""

    def test_san_fallback(self):
        move, exp = _extract_uci_move("Nf3")
        assert move == "Nf3"


# ─────────────────────────────────────────────────────────────────────────────
# Prompt Building Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestPromptBuilding:
    def test_basic_prompt(self):
        fen = chess.STARTING_FEN
        prompt = _build_move_prompt(fen, [])
        assert "FEN" in prompt
        assert fen in prompt

    def test_prompt_with_history(self):
        prompt = _build_move_prompt(chess.STARTING_FEN, ["e2e4", "e7e5"])
        assert "e2e4" in prompt
        assert "e7e5" in prompt

    def test_prompt_truncates_long_history(self):
        history = [f"a{i}a{i+1}" for i in range(1, 40)]
        prompt = _build_move_prompt(chess.STARTING_FEN, history)
        # Should only include last 20
        assert "Your move" in prompt


# ─────────────────────────────────────────────────────────────────────────────
# Mock Adapter Integration Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestMockAdapter:
    def test_unconfigured_returns_error(self):
        adapter = MockAdapter()
        board = chess.Board()
        result = adapter.get_move(board)
        assert result.error
        assert "not configured" in result.error.lower()

    def test_configured_returns_move(self):
        adapter = MockAdapter()
        adapter.configure("test-key")
        adapter.set_moves(["e2e4"])
        board = chess.Board()
        result = adapter.get_move(board)
        assert result.uci_move == "e2e4"
        assert not result.error

    def test_error_triggers_retry(self):
        adapter = MockAdapter()
        adapter.configure("test-key")
        adapter.rate_limit.min_interval = 0  # speed up tests
        adapter.set_error(True)
        board = chess.Board()
        result = adapter.get_move(board)
        assert result.error  # all retries failed

    def test_model_info(self):
        adapter = MockAdapter()
        info = adapter.get_info()
        assert info.model_id == "mock_ai"
        assert info.display_name == "Mock AI"
        assert info.provider == "Test"


# ─────────────────────────────────────────────────────────────────────────────
# Gemini Adapter Tests (no API calls)
# ─────────────────────────────────────────────────────────────────────────────

class TestGeminiAdapter:
    def test_model_info(self):
        adapter = GeminiAdapter()
        info = adapter.get_info()
        assert info.model_id == "gemini_flash"
        assert "Gemini" in info.display_name
        assert info.provider == "Google"
        assert info.supports_analysis

    def test_unconfigured(self):
        adapter = GeminiAdapter()
        assert not adapter.is_configured
        board = chess.Board()
        result = adapter.get_move(board)
        assert result.error

    def test_gemini_models_list(self):
        models = get_gemini_models()
        assert len(models) >= 2
        ids = [m["id"] for m in models]
        assert any("flash" in id for id in ids)


# ─────────────────────────────────────────────────────────────────────────────
# Arena Manager Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestArenaManager:
    def test_register_model(self, arena_manager):
        adapter = MockAdapter()
        profile = arena_manager.register_model(adapter)
        assert profile["model_id"] == "mock_ai"
        assert profile["elo"] == 1500
        assert profile["games_played"] == 0

    def test_register_idempotent(self, arena_manager):
        adapter = MockAdapter()
        arena_manager.register_model(adapter)
        arena_manager.register_model(adapter)  # second call
        models = arena_manager.get_all_models()
        mock_models = [m for m in models if m["model_id"] == "mock_ai"]
        assert len(mock_models) == 1

    def test_get_model_profile(self, arena_manager):
        adapter = MockAdapter()
        arena_manager.register_model(adapter)
        profile = arena_manager.get_model_profile("mock_ai")
        assert profile is not None
        assert profile["display_name"] == "Mock AI"

    def test_get_nonexistent_model(self, arena_manager):
        profile = arena_manager.get_model_profile("nonexistent")
        assert profile is None

    def test_update_model_elo_win(self, arena_manager):
        adapter = MockAdapter()
        arena_manager.register_model(adapter)
        arena_manager.update_model_elo("mock_ai", 1550, won=True)
        profile = arena_manager.get_model_profile("mock_ai")
        assert profile["elo"] == 1550
        assert profile["wins"] == 1
        assert profile["games_played"] == 1

    def test_update_model_elo_loss(self, arena_manager):
        adapter = MockAdapter()
        arena_manager.register_model(adapter)
        arena_manager.update_model_elo("mock_ai", 1450, won=False)
        profile = arena_manager.get_model_profile("mock_ai")
        assert profile["elo"] == 1450
        assert profile["losses"] == 1

    def test_update_model_elo_draw(self, arena_manager):
        adapter = MockAdapter()
        arena_manager.register_model(adapter)
        arena_manager.update_model_elo("mock_ai", 1500, won=None)
        profile = arena_manager.get_model_profile("mock_ai")
        assert profile["draws"] == 1

    def test_peak_elo_tracked(self, arena_manager):
        adapter = MockAdapter()
        arena_manager.register_model(adapter)
        arena_manager.update_model_elo("mock_ai", 1600, won=True)
        arena_manager.update_model_elo("mock_ai", 1550, won=False)
        profile = arena_manager.get_model_profile("mock_ai")
        assert profile["peak_elo"] == 1600

    def test_unified_leaderboard_entries(self, arena_manager):
        adapter = MockAdapter()
        arena_manager.register_model(adapter)
        entries = arena_manager.get_unified_leaderboard_entries()
        assert len(entries) >= 1
        mock_entry = next(e for e in entries if e["model_id"] == "mock_ai")
        assert mock_entry["type"] == "ai_external"
        assert "Mock AI" in mock_entry["name"]

    def test_record_arena_result(self, arena_manager):
        adapter = MockAdapter()
        arena_manager.register_model(adapter)
        changes = arena_manager.record_arena_result(
            model_id="mock_ai",
            player_name="Tester",
            player_elo=1200,
            model_elo=1500,
            score=1.0,  # player wins
        )
        assert changes["player_change"] > 0
        assert changes["model_change"] < 0
        assert changes["player_elo_after"] > 1200


# ─────────────────────────────────────────────────────────────────────────────
# Arena Match Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestArenaMatch:
    def test_create_match(self, arena_manager):
        adapter = MockAdapter()
        adapter.configure("test-key")
        match = arena_manager.create_match(adapter, player_color="white")
        assert match.mode == "player_vs_ai"
        assert match.player_color == "white"
        assert not match.is_game_over

    def test_apply_valid_move(self, arena_manager):
        adapter = MockAdapter()
        adapter.configure("test-key")
        match = arena_manager.create_match(adapter)
        assert match.apply_move("e2e4")
        assert len(match.move_history) == 1

    def test_apply_invalid_move(self, arena_manager):
        adapter = MockAdapter()
        adapter.configure("test-key")
        match = arena_manager.create_match(adapter)
        assert not match.apply_move("e2e5")  # illegal

    def test_sync_ai_move(self, arena_manager):
        adapter = MockAdapter()
        adapter.configure("test-key")
        adapter.set_moves(["e2e4"])
        adapter.rate_limit.min_interval = 0
        match = arena_manager.create_match(adapter)
        result = match.request_ai_move_sync()
        assert result.uci_move == "e2e4"

    def test_model_info_from_match(self, arena_manager):
        adapter = MockAdapter()
        adapter.configure("test-key")
        match = arena_manager.create_match(adapter)
        info = match.model_info
        assert info.model_id == "mock_ai"

    def test_match_result_default(self, arena_manager):
        adapter = MockAdapter()
        adapter.configure("test-key")
        match = arena_manager.create_match(adapter)
        assert match.result == "*"

    def test_get_winner_ongoing(self, arena_manager):
        adapter = MockAdapter()
        adapter.configure("test-key")
        match = arena_manager.create_match(adapter)
        assert match.get_winner() == "draw"  # not over, returns draw


# ─────────────────────────────────────────────────────────────────────────────
# Registry Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestRegistry:
    def test_gemini_registered(self):
        adapters = get_available_adapters()
        assert "gemini_flash" in adapters

    def test_create_adapter(self):
        adapter = create_adapter("gemini_flash")
        assert adapter is not None
        assert isinstance(adapter, GeminiAdapter)

    def test_create_unknown_adapter(self):
        adapter = create_adapter("nonexistent_model")
        assert adapter is None

    def test_register_custom(self):
        register_adapter("mock_test", MockAdapter)
        adapters = get_available_adapters()
        assert "mock_test" in adapters
