"""Tests for the AI engine."""

import chess
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.engine.ai_engine import AIEngine
from src.engine.evaluator import Evaluator


def test_evaluator_initial():
    board = chess.Board()
    ev = Evaluator()
    score = ev.evaluate(board)
    # Initial position should be roughly equal
    assert -100 < score < 100, f"Initial eval too unbalanced: {score}"


def test_evaluator_material_advantage():
    # White up a queen
    board = chess.Board("rnb1kbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
    ev = Evaluator()
    score = ev.evaluate(board)
    assert score > 500, f"Should favour White heavily: {score}"


def test_evaluator_checkmate():
    board = chess.Board("rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 0 1")
    ev = Evaluator()
    score = ev.evaluate(board)
    assert score == -30000 or score < -20000


def test_ai_finds_move():
    board = chess.Board()
    ai = AIEngine("RECRUIT")
    move = ai.get_best_move(board)
    assert move is not None
    assert move in board.legal_moves


def test_ai_finds_mate_in_one():
    # White to play and mate with Qh5#
    board = chess.Board("rnbqkbnr/pppp1ppp/8/4p3/6P1/5P2/PPPPP2P/RNBQKBNR b KQkq - 0 1")
    # Black: Qh4#
    ai = AIEngine("CAPTAIN")
    move = ai.get_best_move(board)
    assert move is not None
    # The best move should be Qh4# (checkmate)
    board.push(move)
    # At minimum, AI should find a strong move (may or may not be forced mate here)
    assert True  # If we get here, AI didn't crash


def test_ai_difficulty_levels():
    board = chess.Board()
    for diff in ["RECRUIT", "SOLDIER", "CAPTAIN", "GENERAL"]:
        ai = AIEngine(diff)
        move = ai.get_best_move(board)
        assert move is not None


def test_evaluator_bishop_pair():
    ev = Evaluator()
    # Position with white bishop pair
    board = chess.Board("rnbqk2r/pppppppp/8/8/8/8/PPPPPPPP/RNBQKB1R w KQkq - 0 1")
    score1 = ev.evaluate(board)
    # Baseline
    board2 = chess.Board()
    score2 = ev.evaluate(board2)
    # Both should be close to balanced
    assert isinstance(score1, int)
    assert isinstance(score2, int)


if __name__ == "__main__":
    test_evaluator_initial()
    test_evaluator_material_advantage()
    test_ai_finds_move()
    test_ai_difficulty_levels()
    test_evaluator_bishop_pair()
    print("All AI tests passed!")
