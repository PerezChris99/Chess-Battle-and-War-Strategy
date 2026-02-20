"""Tests for the chess engine wrapper."""

import chess
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.engine.chess_engine import ChessEngine


def test_initial_position():
    engine = ChessEngine()
    assert engine.turn == chess.WHITE
    assert engine.fullmove_number == 1
    assert not engine.is_check
    assert not engine.is_game_over
    assert len(engine.legal_moves) == 20


def test_make_move():
    engine = ChessEngine()
    san = engine.make_move_uci("e2e4")
    assert san == "e4"
    assert engine.turn == chess.BLACK
    assert engine.move_count == 1


def test_undo_move():
    engine = ChessEngine()
    engine.make_move_uci("e2e4")
    engine.make_move_uci("e7e5")
    engine.undo_move()
    assert engine.turn == chess.BLACK
    assert engine.move_count == 1


def test_promotion_detection():
    engine = ChessEngine("8/P7/8/8/8/8/8/4K2k w - - 0 1")
    assert engine.is_promotion_move(chess.A7, chess.A8)


def test_legal_moves_from():
    engine = ChessEngine()
    moves = engine.get_legal_moves_from(chess.E2)
    assert len(moves) == 2  # e3 and e4


def test_pgn_export():
    engine = ChessEngine()
    engine.make_move_uci("e2e4")
    engine.make_move_uci("e7e5")
    pgn = engine.to_pgn()
    assert "e4" in pgn
    assert "e5" in pgn


def test_copy():
    engine = ChessEngine()
    engine.make_move_uci("e2e4")
    copy = engine.copy()
    copy.make_move_uci("e7e5")
    assert engine.move_count == 1
    assert copy.move_count == 2


if __name__ == "__main__":
    test_initial_position()
    test_make_move()
    test_undo_move()
    test_promotion_detection()
    test_legal_moves_from()
    test_pgn_export()
    test_copy()
    print("All engine tests passed!")
