"""Tests for Phase 6 — Sound, Save/Load, Post-Game Analysis."""

import os
import sys
import tempfile
import shutil

import chess
import pytest

# Ensure project root is on the path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.game.move_history import MoveHistory
from src.game.save_load import SaveLoadManager
from src.game.post_game_analysis import PostGameAnalyzer, GameAnalysis


# ── Save/Load Tests ─────────────────────────────────────────


class TestSaveLoad:
    """Test PGN save and load functionality."""

    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self.manager = SaveLoadManager()
        # Override save dir to temp
        import src.game.save_load as sl
        self._orig_dir = sl.SAVES_DIR
        sl.SAVES_DIR = self.tmpdir

    def teardown_method(self):
        import src.game.save_load as sl
        sl.SAVES_DIR = self._orig_dir
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_save_and_load(self):
        """Save a game and load it back."""
        board = chess.Board()
        history = MoveHistory()

        # Play e4 e5
        move1 = chess.Move.from_uci("e2e4")
        history.add_move("e4", "e2e4", "Infantry advances", 1, True, False, False, False, False, None)
        board.push(move1)

        move2 = chess.Move.from_uci("e7e5")
        history.add_move("e5", "e7e5", "Infantry counters", 1, False, False, False, False, False, None)
        board.push(move2)

        filepath = self.manager.save_game(
            board, history, "white", "SOLDIER", "King's Pawn", "*"
        )
        assert os.path.exists(filepath)

        data = self.manager.load_game(filepath)
        assert data is not None
        assert len(data["moves"]) == 2
        assert data["moves"][0]["san"] == "e4"
        assert data["moves"][1]["san"] == "e5"

    def test_list_saves(self):
        """List saved games."""
        board = chess.Board()
        history = MoveHistory()
        history.add_move("e4", "e2e4", "Test", 1, True, False, False, False, False, None)
        board.push(chess.Move.from_uci("e2e4"))

        self.manager.save_game(board, history, "white", "SOLDIER", "", "*", "test1.pgn")
        self.manager.save_game(board, history, "white", "CAPTAIN", "", "*", "test2.pgn")

        saves = self.manager.list_saves()
        assert len(saves) >= 2

    def test_export_pgn_string(self):
        """Export PGN as string."""
        board = chess.Board()
        history = MoveHistory()
        history.add_move("d4", "d2d4", "Queen pawn advance", 1, True, False, False, False, False, None)
        board.push(chess.Move.from_uci("d2d4"))

        pgn = self.manager.export_pgn_string(board, history, "white", "GENERAL", "*")
        assert "d4" in pgn
        assert "Chess Battle" in pgn

    def test_delete_save(self):
        """Delete a saved file."""
        board = chess.Board()
        history = MoveHistory()
        board.push(chess.Move.from_uci("e2e4"))
        history.add_move("e4", "e2e4", "Test", 1, True, False, False, False, False, None)

        filepath = self.manager.save_game(board, history, filename="delete_me.pgn")
        assert os.path.exists(filepath)
        assert self.manager.delete_save(filepath)
        assert not os.path.exists(filepath)

    def test_load_nonexistent(self):
        """Loading a nonexistent file returns None."""
        assert self.manager.load_game("/nonexistent/file.pgn") is None


# ── Post-Game Analysis Tests ────────────────────────────────


class TestPostGameAnalysis:
    """Test the battle report generator."""

    def test_basic_analysis(self):
        """Analyze a short game."""
        analyzer = PostGameAnalyzer()
        history = MoveHistory()
        board = chess.Board()

        # Play scholars mate: 1.e4 e5 2.Bc4 Nc6 3.Qh5 Nf6 4.Qxf7#
        moves = [
            ("e4", "e2e4", True, 1),
            ("e5", "e7e5", False, 1),
            ("Bc4", "f1c4", True, 2),
            ("Nc6", "b8c6", False, 2),
            ("Qh5", "d1h5", True, 3),
            ("Nf6", "g8f6", False, 3),
            ("Qxf7#", "h5f7", True, 4),
        ]

        for san, uci, is_white, mn in moves:
            move = chess.Move.from_uci(uci)
            is_cap = board.is_capture(move)
            history.add_move(san, uci, f"Move {san}", mn, is_white, is_cap, False, False, False, None)
            board.push(move)

        analysis = analyzer.analyze(history, board, "Scholar's Mate", "1-0")
        assert analysis.total_moves == 7
        assert analysis.game_result == "1-0"
        assert len(analysis.assessments) == 7
        assert "BATTLE REPORT" in analysis.battle_report
        assert analysis.white_accuracy > 0

    def test_empty_game(self):
        """Analyze a game with no moves."""
        analyzer = PostGameAnalyzer()
        history = MoveHistory()
        board = chess.Board()

        analysis = analyzer.analyze(history, board, result="*")
        assert analysis.total_moves == 0
        assert "idle" in analysis.battle_report.lower()

    def test_classification_thresholds(self):
        """Verify move classifications use correct thresholds."""
        analyzer = PostGameAnalyzer()
        assert analyzer._classify_move(0) == "best"
        assert analyzer._classify_move(10) == "best"
        assert analyzer._classify_move(25) == "excellent"
        assert analyzer._classify_move(40) == "good"
        assert analyzer._classify_move(55) == "inaccuracy"
        assert analyzer._classify_move(110) == "mistake"
        assert analyzer._classify_move(250) == "blunder"


# ── Sound Manager Tests ─────────────────────────────────────


class TestSoundManager:
    """Test sound manager (without actually playing audio)."""

    def test_import(self):
        """SoundManager imports correctly."""
        from src.game.sound_manager import SoundManager
        # Just verify it can be imported
        assert SoundManager is not None

    def test_disabled_play(self):
        """Playing while disabled does nothing (no crash)."""
        from src.game.sound_manager import SoundManager
        sm = SoundManager(enabled=False)
        sm.play("move")       # Should not crash
        sm.play("capture")    # Should not crash
        sm.play("nonexistent")  # Should not crash

    def test_volume_clamping(self):
        """Volume is clamped to [0, 1]."""
        from src.game.sound_manager import SoundManager
        sm = SoundManager(enabled=False)
        sm.set_volume(1.5)
        assert sm.volume == 1.0
        sm.set_volume(-0.5)
        assert sm.volume == 0.0
