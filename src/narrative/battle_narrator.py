"""
Battle narrator — transforms chess moves into immersive war narratives.

This is the core narrative engine that converts python-chess moves into
battle descriptions, complete with military terminology, tactical analysis,
and dramatic flair.
"""

from __future__ import annotations

import chess
import random

from .piece_lore import (
    get_piece_lore, get_terrain_name, get_army_name, get_army_adjective, PIECE_LORE,
)
from .scenarios import (
    get_random, get_opening_scenario, get_middlegame_transition,
    get_endgame_scenario, get_checkmate_narrative, get_check_narrative,
    CAPTURE_SCENARIOS, CASTLING_SCENARIOS, EN_PASSANT_SCENARIOS,
    PROMOTION_SCENARIOS, TACTICAL_SCENARIOS,
)
from src.utils.helpers import get_game_phase, piece_full_name, square_name


class BattleNarrator:
    """Converts chess moves into battle narratives."""

    def __init__(self):
        self._last_phase = "opening"
        self._move_count = 0
        self._phase_announced = {"opening": False, "middlegame": False, "endgame": False}

    def reset(self) -> None:
        """Reset narrator state for a new game."""
        self._last_phase = "opening"
        self._move_count = 0
        self._phase_announced = {"opening": False, "middlegame": False, "endgame": False}

    def get_opening_text(self) -> str:
        """Get the introductory battle scene text."""
        return get_opening_scenario()

    def narrate_move(self, board: chess.Board, move: chess.Move) -> str:
        """Generate a battle narrative for a move (BEFORE the move is pushed).

        Args:
            board: Current board state (move NOT yet applied).
            move:  The move about to be made.

        Returns:
            A narrative string describing the move in military terms.
        """
        self._move_count += 1
        narratives: list[str] = []

        # Phase transition announcements
        phase = get_game_phase(board)
        if phase != self._last_phase and not self._phase_announced[phase]:
            if phase == "middlegame":
                narratives.append(get_middlegame_transition())
            elif phase == "endgame":
                narratives.append(get_endgame_scenario())
            self._phase_announced[phase] = True
            self._last_phase = phase

        # Determine move type and build narrative
        piece = board.piece_at(move.from_square)
        if not piece:
            return "A mysterious move occurs on the battlefield..."

        is_white = piece.color == chess.WHITE
        army = get_army_adjective(is_white)
        lore = get_piece_lore(piece.symbol())
        from_name = square_name(move.from_square)
        to_name = square_name(move.to_square)
        terrain = get_terrain_name(to_name)

        # ── Special moves ───────────────────────────────────────

        # Castling
        if board.is_castling(move):
            side = "kingside" if board.is_kingside_castling(move) else "queenside"
            narratives.append(get_random(CASTLING_SCENARIOS[side]))
            return " ".join(narratives)

        # En passant
        if board.is_en_passant(move):
            narratives.append(get_random(EN_PASSANT_SCENARIOS))
            if board.gives_check(move):
                narratives.append(get_check_narrative())
            return " ".join(narratives)

        # Promotion
        if move.promotion:
            promo_symbol = chess.piece_symbol(move.promotion).upper()
            promo_templates = PROMOTION_SCENARIOS.get(promo_symbol, PROMOTION_SCENARIOS["Q"])
            narratives.append(get_random(promo_templates))
            if board.gives_check(move):
                narratives.append(get_check_narrative())
            return " ".join(narratives)

        # ── Captures ────────────────────────────────────────────

        if board.is_capture(move):
            victim_piece = board.piece_at(move.to_square)
            if victim_piece:
                victim_lore = get_piece_lore(victim_piece.symbol())
                attacker_name = f"{army} {lore['title']}"
                victim_name = victim_lore["title"]

                # Choose capture verb
                verb = random.choice(lore["capture_verbs"])

                # Major or minor capture
                victim_val = {"K": 6, "Q": 5, "R": 4, "B": 3, "N": 3, "P": 1}
                importance = victim_val.get(victim_piece.symbol().upper(), 1)

                if importance >= 4:
                    template_set = CAPTURE_SCENARIOS["major"]
                elif piece.symbol().upper() == "P":
                    template_set = CAPTURE_SCENARIOS["pawn_takes"]
                else:
                    template_set = CAPTURE_SCENARIOS["minor"]

                narratives.append(get_random(
                    template_set,
                    attacker=attacker_name,
                    victim=victim_name,
                ))
            else:
                narratives.append(f"The {army} {lore['title']} captures at {terrain}.")

        # ── Quiet moves ─────────────────────────────────────────

        else:
            verb = random.choice(lore["move_verbs"])
            if piece.piece_type == chess.PAWN:
                # Double pawn push
                rank_diff = abs(chess.square_rank(move.to_square) - chess.square_rank(move.from_square))
                if rank_diff == 2:
                    narratives.append(
                        f"The {army} Infantry charges forward with a double advance to {terrain}!"
                    )
                else:
                    narratives.append(
                        f"The {army} {lore['title']} {verb} {to_name} ({terrain})."
                    )
            else:
                narratives.append(
                    f"The {army} {lore['title']} {verb} {to_name} — "
                    f"taking position at {terrain}."
                )

        # ── Check / Checkmate amendments ────────────────────────

        if board.gives_check(move):
            # Check if this is checkmate
            board.push(move)
            is_mate = board.is_checkmate()
            board.pop()

            if is_mate:
                narratives.append(get_checkmate_narrative())
            else:
                narratives.append(get_check_narrative())

        return " ".join(narratives)

    def narrate_game_result(self, board: chess.Board) -> str:
        """Generate narrative for the game's conclusion."""
        from .scenarios import get_result_narrative

        if board.is_checkmate():
            winner = "black_wins" if board.turn == chess.WHITE else "white_wins"
            return get_result_narrative(winner)
        elif board.is_stalemate():
            return get_result_narrative("stalemate")
        else:
            return get_result_narrative("draw")

    def get_tactical_hint(self, board: chess.Board, move: chess.Move) -> str | None:
        """Check if a move creates a tactical motif and describe it."""
        board.push(move)

        hints = []

        # Check for forks (piece attacking 2+ valuable pieces)
        piece = board.piece_at(move.to_square)
        if piece:
            attacked_value = 0
            attacked_count = 0
            for sq in board.attacks(move.to_square):
                target = board.piece_at(sq)
                if target and target.color != piece.color:
                    val = {"K": 6, "Q": 5, "R": 4, "B": 3, "N": 3, "P": 1}
                    attacked_value += val.get(target.symbol().upper(), 1)
                    attacked_count += 1

            if attacked_count >= 2 and attacked_value >= 6:
                piece_name = get_piece_lore(piece.symbol())["title"]
                hints.append(get_random(
                    TACTICAL_SCENARIOS["fork"],
                    piece=piece_name,
                ))

        board.pop()
        return " ".join(hints) if hints else None
