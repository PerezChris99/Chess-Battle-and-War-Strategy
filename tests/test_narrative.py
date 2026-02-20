"""Tests for the battle narrative system."""

import chess
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.narrative.battle_narrator import BattleNarrator
from src.narrative.piece_lore import get_piece_lore, get_terrain_name, get_army_name
from src.narrative.scenarios import get_opening_scenario, get_checkmate_narrative


def test_piece_lore():
    lore = get_piece_lore("K")
    assert lore["title"] == "Supreme Commander"
    assert "Commander" in lore["description"]

    lore_q = get_piece_lore("Q")
    assert lore_q["title"] == "Grand General"

    lore_n = get_piece_lore("N")
    assert "Cavalry" in lore_n["title"]


def test_terrain_names():
    assert "stronghold" in get_terrain_name("d4")
    assert "heart" in get_terrain_name("d5")
    # Generic terrain
    terrain = get_terrain_name("b3")
    assert len(terrain) > 0


def test_army_names():
    assert "White" in get_army_name(True)
    assert "Black" in get_army_name(False)


def test_opening_scenario():
    text = get_opening_scenario()
    assert len(text) > 20


def test_checkmate_narrative():
    text = get_checkmate_narrative()
    assert "CHECKMATE" in text or "victory" in text.lower() or "fallen" in text.lower()


def test_narrator_basic_move():
    narrator = BattleNarrator()
    board = chess.Board()
    move = chess.Move.from_uci("e2e4")
    narrative = narrator.narrate_move(board, move)
    assert len(narrative) > 10
    assert "Infantry" in narrative or "marches" in narrative or "advances" in narrative or "charges" in narrative


def test_narrator_capture():
    board = chess.Board("rnbqkbnr/ppp1pppp/8/3p4/4P3/8/PPPP1PPP/RNBQKBNR w KQkq d6 0 2")
    narrator = BattleNarrator()
    move = chess.Move.from_uci("e4d5")
    narrative = narrator.narrate_move(board, move)
    assert len(narrative) > 10


def test_narrator_castling():
    board = chess.Board("r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4")
    narrator = BattleNarrator()
    move = chess.Move.from_uci("e1g1")
    narrative = narrator.narrate_move(board, move)
    assert "fortif" in narrative.lower() or "castle" in narrative.lower() or "bunker" in narrative.lower()


def test_narrator_reset():
    narrator = BattleNarrator()
    narrator.reset()
    text = narrator.get_opening_text()
    assert len(text) > 0


if __name__ == "__main__":
    test_piece_lore()
    test_terrain_names()
    test_army_names()
    test_opening_scenario()
    test_checkmate_narrative()
    test_narrator_basic_move()
    test_narrator_capture()
    test_narrator_castling()
    test_narrator_reset()
    print("All narrative tests passed!")
